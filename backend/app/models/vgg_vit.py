from __future__ import annotations

import importlib

import torch
import torch.nn as nn


def conv_bn_relu(in_c: int, out_c: int, kernel_size=3, stride=1, padding=1) -> nn.Sequential:
    return nn.Sequential(
        nn.Conv2d(
            in_c,
            out_c,
            kernel_size=kernel_size,
            stride=stride,
            padding=padding,
            bias=False,
        ),
        nn.BatchNorm2d(out_c),
        nn.ReLU(inplace=True),
    )


class VGG16Blocks(nn.Module):
    def __init__(self, pretrained: bool = False, to_pool3: bool = True) -> None:
        super().__init__()
        tv_models = importlib.import_module("torchvision.models")
        if pretrained:
            weights = getattr(tv_models, "VGG16_Weights", None)
            model = tv_models.vgg16(weights=weights.IMAGENET1K_V1 if weights else "IMAGENET1K_V1")
        else:
            model = tv_models.vgg16(weights=None)

        if to_pool3:
            self.features = nn.Sequential(*list(model.features.children())[:17])
            self.out_channels = 256
        else:
            self.features = nn.Sequential(*list(model.features.children())[:10])
            self.out_channels = 128

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.features(x)


class InceptionV7(nn.Module):
    def __init__(
        self,
        in_channels: int = 256,
        out_channels: int = 512,
        branch_channels: int = 128,
        dropout: float = 0.0,
    ) -> None:
        super().__init__()
        b = branch_channels

        self.branch1 = conv_bn_relu(in_channels, b, kernel_size=1, stride=1, padding=0)

        self.branch2 = nn.Sequential(
            conv_bn_relu(in_channels, b, kernel_size=1, stride=1, padding=0),
            conv_bn_relu(b, b, kernel_size=(3, 1), stride=1, padding=(1, 0)),
            conv_bn_relu(b, b, kernel_size=(1, 3), stride=1, padding=(0, 1)),
        )

        self.branch3 = nn.Sequential(
            conv_bn_relu(in_channels, b, kernel_size=1, stride=1, padding=0),
            conv_bn_relu(b, b, kernel_size=(3, 1), stride=1, padding=(1, 0)),
            conv_bn_relu(b, b, kernel_size=(1, 3), stride=1, padding=(0, 1)),
            conv_bn_relu(b, b, kernel_size=(3, 1), stride=1, padding=(1, 0)),
            conv_bn_relu(b, b, kernel_size=(1, 3), stride=1, padding=(0, 1)),
        )

        self.branch4 = nn.Sequential(
            nn.MaxPool2d(3, stride=1, padding=1),
            conv_bn_relu(in_channels, b, kernel_size=1, stride=1, padding=0),
        )

        self.proj = conv_bn_relu(b * 4, out_channels, kernel_size=1, stride=1, padding=0)
        self.dropout = nn.Dropout2d(p=dropout) if dropout > 0 else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x1 = self.branch1(x)
        x2 = self.branch2(x)
        x3 = self.branch3(x)
        x4 = self.branch4(x)
        out = torch.cat([x1, x2, x3, x4], dim=1)
        out = self.proj(out)
        out = self.dropout(out)
        return out


class SpatialReducer(nn.Module):
    def __init__(self, in_channels: int = 512, out_channels: int = 512, stride: int = 4) -> None:
        super().__init__()
        self.reduce = conv_bn_relu(
            in_channels,
            out_channels,
            kernel_size=3,
            stride=stride,
            padding=1,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.reduce(x)


class PatchEncoder(nn.Module):
    def __init__(self, in_c: int = 512, emb_dim: int = 32, grid_size: tuple[int, int] = (7, 7)) -> None:
        super().__init__()
        self.grid_h, self.grid_w = grid_size
        self.num_patches = self.grid_h * self.grid_w
        self.proj = nn.Linear(in_c, emb_dim)
        self.pos_embed = nn.Parameter(torch.randn(1, self.num_patches, emb_dim) * 0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, c, h, w = x.shape
        if h != self.grid_h or w != self.grid_w:
            raise ValueError(f"Expected grid {self.grid_h}x{self.grid_w}, got {h}x{w}")
        x = x.permute(0, 2, 3, 1).reshape(b, h * w, c)
        x = self.proj(x)
        x = x + self.pos_embed
        return x


class ViTEncoder(nn.Module):
    def __init__(
        self,
        emb_dim: int = 32,
        depth: int = 6,
        heads: int = 4,
        mlp_dim: int = 128,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        if emb_dim % heads != 0:
            raise ValueError("emb_dim must be divisible by heads")

        self.layers = nn.ModuleList(
            [
                nn.TransformerEncoderLayer(
                    d_model=emb_dim,
                    nhead=heads,
                    dim_feedforward=mlp_dim,
                    dropout=dropout,
                    batch_first=True,
                    norm_first=True,
                )
                for _ in range(depth)
            ]
        )
        self.final_norm = nn.LayerNorm(emb_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for layer in self.layers:
            x = layer(x)
        return self.final_norm(x)


class AttentionPool(nn.Module):
    def __init__(self, emb_dim: int) -> None:
        super().__init__()
        self.attn = nn.Linear(emb_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        scores = self.attn(x)
        weights = torch.softmax(scores, dim=1)
        return (x * weights).sum(dim=1)


class PlantXViT_v2(nn.Module):
    def __init__(
        self,
        num_classes: int = 7,
        emb_dim: int = 32,
        pretrained_vgg: bool = False,
        use_pool3: bool = True,
        inception_out_channels: int = 512,
        reducer_stride: int = 4,
        vit_depth: int = 6,
        vit_heads: int = 4,
        vit_mlp: int = 128,
        vit_dropout: float = 0.1,
        classifier_dropout: float = 0.3,
    ) -> None:
        super().__init__()

        self.vgg = VGG16Blocks(pretrained=pretrained_vgg, to_pool3=use_pool3)
        vgg_out_c = self.vgg.out_channels
        self.inception = InceptionV7(
            in_channels=vgg_out_c,
            out_channels=inception_out_channels,
            branch_channels=128,
            dropout=0.0,
        )
        self.reducer = SpatialReducer(
            in_channels=inception_out_channels,
            out_channels=inception_out_channels,
            stride=reducer_stride,
        )
        self.patch_encoder = PatchEncoder(in_c=inception_out_channels, emb_dim=emb_dim, grid_size=(7, 7))
        self.transformer = ViTEncoder(
            emb_dim=emb_dim,
            depth=vit_depth,
            heads=vit_heads,
            mlp_dim=vit_mlp,
            dropout=vit_dropout,
        )

        self.attn_pool = AttentionPool(emb_dim)
        self.norm = nn.LayerNorm(emb_dim)
        self.dropout = nn.Dropout(classifier_dropout)
        self.classifier = nn.Linear(emb_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.vgg(x)
        x = self.inception(x)
        x = self.reducer(x)
        x = self.patch_encoder(x)
        x = self.transformer(x)
        x = self.attn_pool(x)
        x = self.norm(x)
        x = self.dropout(x)
        return self.classifier(x)


def create_model(num_classes: int = 7) -> nn.Module:
    return PlantXViT_v2(
        num_classes=num_classes,
        emb_dim=32,
        pretrained_vgg=False,
        use_pool3=True,
        inception_out_channels=512,
        reducer_stride=4,
        vit_depth=6,
        vit_heads=4,
        vit_mlp=128,
        vit_dropout=0.1,
        classifier_dropout=0.3,
    )
