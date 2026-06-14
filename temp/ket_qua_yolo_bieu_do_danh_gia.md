# Ket qua YOLO detector va code ve bieu do huan luyen

File nay tong hop so lieu duoc doc tu output trong hai notebook:

- `train files/yolo8s_focalloss.ipynb`
- `train files/yolo11s_focalloss.ipynb`

Khong can train lai. Cac doan code ben duoi doc log da luu trong notebook, trich cac chi so theo epoch thanh mang/DataFrame va ve bieu do.

## 1. Thiet lap thuc nghiem rut gon

| Noi dung | Gia tri |
|---|---|
| Nen tang | Google Colab ket hop Google Drive |
| GPU ghi nhan trong log | Tesla T4, 14913 MiB |
| Dataset | ISIC 2018 Task 1 da chuyen segmentation mask sang bounding box YOLO |
| So lop detector | 1 lop: `lesion` |
| Train images | 1815 |
| Validation images | 389 |
| Test images | 390 |
| Image size | 640 |
| Epochs | 100 |
| Optimizer | AdamW |
| Initial learning rate | 0.01 |
| LR schedule | Cosine LR |
| Patience | 30 |
| Pretrained | True |
| Cache | True |
| Augmentation | degrees=5.0, translate=0.1, scale=0.15, fliplr=0.5, mosaic=0.5, mixup=0.1, copy_paste=0.1 |
| Ultralytics YOLOv8 notebook | ultralytics 8.4.29 |
| Ultralytics YOLOv11 notebook | ultralytics 8.4.53 |

## 2. Bang ket qua danh gia

### 2.1. Ket qua validation sau khi load best model

| Mo hinh | Images | Instances | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 | Inference |
|---|---:|---:|---:|---:|---:|---:|---:|
| YOLOv8s | 389 | 389 | 0.956 | 0.939 | 0.982 | 0.722 | 7.8 ms/anh |
| YOLOv11s | 389 | 389 | 0.937 | 0.916 | 0.974 | 0.681 | 8.3 ms/anh |

### 2.2. Ket qua test set

| Mo hinh | Images | Instances | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 | Inference |
|---|---:|---:|---:|---:|---:|---:|---:|
| YOLOv8s | 390 | 390 | 0.963 | 0.926 | 0.973 | 0.728 | 7.8 ms/anh |
| YOLOv11s | 390 | 390 | 0.930 | 0.903 | 0.956 | 0.675 | 7.5 ms/anh |

### 2.3. Bang so sanh dua vao bao cao

| Mo hinh | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 | Nhan xet |
|---|---:|---:|---:|---:|---|
| YOLOv8s | 0.963 | 0.926 | 0.973 | 0.728 | Dat ket qua tong the cao hon, dac biet o mAP@0.5:0.95 va Recall. |
| YOLOv11s | 0.930 | 0.903 | 0.956 | 0.675 | Mo hinh nhe hon theo log, toc do test tuong duong, nhung do chinh xac thap hon YOLOv8s tren tap test. |

Ket qua cho thay YOLOv8s dat mAP@0.5 va mAP@0.5:0.95 cao hon YOLOv11s tren tap kiem thu. Chi so Recall cua YOLOv8s cung cao hon, dieu nay co y nghia quan trong trong pipeline ho tro chan doan benh da lieu vi viec bo sot vung ton thuong co the lam anh huong den buoc phan loai phia sau.

Luu y: trong ban thao bao cao hien tai, gia tri `mAP@0.5:0.95 = 1503` la khong dung dinh dang chi so mAP. Theo output notebook, gia tri dung tren tap test la `0.728` voi YOLOv8s va `0.675` voi YOLOv11s.

## 3. Code doc so tu notebook va tao mang de ve bieu do

Dat file notebook o dung duong dan trong workspace, sau do chay code nay. Code chi doc output da co trong notebook, khong goi `model.train()`.

```python
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
NUM = r"([0-9]+(?:\.[0-9]+)?(?:e-?\d+)?)"


def extract_yolo_training_rows(notebook_path):
    """Doc output notebook Ultralytics va tra ve DataFrame theo epoch."""
    notebook_path = Path(notebook_path)
    nb = json.loads(notebook_path.read_text(encoding="utf-8"))

    text_parts = []
    for cell in nb.get("cells", []):
        for output in cell.get("outputs", []):
            if "text" in output:
                text_parts.append("".join(output["text"]))

    text = ANSI_RE.sub("", "\n".join(text_parts)).replace("\r", "\n")

    rows = []
    pending_loss = None

    for line in text.splitlines():
        clean = " ".join(line.split())

        loss_match = re.match(
            rf"^(\d{{1,3}})/100\s+\S+\s+{NUM}\s+{NUM}\s+{NUM}\s+",
            clean,
        )
        if loss_match:
            pending_loss = {
                "epoch": int(loss_match.group(1)),
                "box_loss": float(loss_match.group(2)),
                "cls_loss": float(loss_match.group(3)),
                "dfl_loss": float(loss_match.group(4)),
            }
            continue

        metric_match = re.match(
            rf"^all\s+(\d+)\s+(\d+)\s+{NUM}\s+{NUM}\s+{NUM}\s+{NUM}",
            clean,
        )
        if metric_match and pending_loss:
            rows.append(
                {
                    **pending_loss,
                    "images": int(metric_match.group(1)),
                    "instances": int(metric_match.group(2)),
                    "precision": float(metric_match.group(3)),
                    "recall": float(metric_match.group(4)),
                    "map50": float(metric_match.group(5)),
                    "map50_95": float(metric_match.group(6)),
                }
            )
            pending_loss = None

    df = pd.DataFrame(rows)
    if len(df) != 100:
        print(f"Canh bao: {notebook_path} chi trich duoc {len(df)} epoch.")
    return df


yolo8_df = extract_yolo_training_rows("train files/yolo8s_focalloss.ipynb")
yolo11_df = extract_yolo_training_rows("train files/yolo11s_focalloss.ipynb")

# Neu can mang Python rieng:
yolo8_epochs = yolo8_df["epoch"].to_list()
yolo8_box_loss = yolo8_df["box_loss"].to_list()
yolo8_cls_loss = yolo8_df["cls_loss"].to_list()
yolo8_dfl_loss = yolo8_df["dfl_loss"].to_list()
yolo8_precision = yolo8_df["precision"].to_list()
yolo8_recall = yolo8_df["recall"].to_list()
yolo8_map50 = yolo8_df["map50"].to_list()
yolo8_map50_95 = yolo8_df["map50_95"].to_list()

yolo11_epochs = yolo11_df["epoch"].to_list()
yolo11_box_loss = yolo11_df["box_loss"].to_list()
yolo11_cls_loss = yolo11_df["cls_loss"].to_list()
yolo11_dfl_loss = yolo11_df["dfl_loss"].to_list()
yolo11_precision = yolo11_df["precision"].to_list()
yolo11_recall = yolo11_df["recall"].to_list()
yolo11_map50 = yolo11_df["map50"].to_list()
yolo11_map50_95 = yolo11_df["map50_95"].to_list()
```

## 4. Code ve bieu do rieng cho tung mo hinh

```python
def plot_single_yolo_training(df, model_name, save_path=None):
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(f"Ket qua huan luyen {model_name}", fontsize=16, fontweight="bold")

    axes[0, 0].plot(df["epoch"], df["box_loss"], label="Box loss")
    axes[0, 0].plot(df["epoch"], df["cls_loss"], label="Cls loss")
    axes[0, 0].plot(df["epoch"], df["dfl_loss"], label="DFL loss")
    axes[0, 0].set_title("Training loss")
    axes[0, 0].set_xlabel("Epoch")
    axes[0, 0].set_ylabel("Loss")
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].legend()

    axes[0, 1].plot(df["epoch"], df["precision"], color="#1f77b4")
    axes[0, 1].set_title("Precision")
    axes[0, 1].set_xlabel("Epoch")
    axes[0, 1].set_ylabel("Precision")
    axes[0, 1].set_ylim(0, 1.05)
    axes[0, 1].grid(True, alpha=0.3)

    axes[1, 0].plot(df["epoch"], df["recall"], color="#2ca02c")
    axes[1, 0].set_title("Recall")
    axes[1, 0].set_xlabel("Epoch")
    axes[1, 0].set_ylabel("Recall")
    axes[1, 0].set_ylim(0, 1.05)
    axes[1, 0].grid(True, alpha=0.3)

    axes[1, 1].plot(df["epoch"], df["map50"], label="mAP@0.5", color="#d62728")
    axes[1, 1].plot(df["epoch"], df["map50_95"], label="mAP@0.5:0.95", color="#9467bd")
    axes[1, 1].set_title("mAP")
    axes[1, 1].set_xlabel("Epoch")
    axes[1, 1].set_ylabel("mAP")
    axes[1, 1].set_ylim(0, 1.05)
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].legend()

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()


plot_single_yolo_training(yolo8_df, "YOLOv8s", "yolov8s_training_curves.png")
plot_single_yolo_training(yolo11_df, "YOLOv11s", "yolov11s_training_curves.png")
```

## 5. Code ve bieu do so sanh YOLOv8s va YOLOv11s

```python
def plot_compare_yolo_training(yolo8_df, yolo11_df, save_path=None):
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("So sanh ket qua huan luyen YOLOv8s va YOLOv11s", fontsize=16, fontweight="bold")

    yolo8_total_loss = yolo8_df["box_loss"] + yolo8_df["cls_loss"] + yolo8_df["dfl_loss"]
    yolo11_total_loss = yolo11_df["box_loss"] + yolo11_df["cls_loss"] + yolo11_df["dfl_loss"]

    axes[0, 0].plot(yolo8_df["epoch"], yolo8_total_loss, label="YOLOv8s")
    axes[0, 0].plot(yolo11_df["epoch"], yolo11_total_loss, label="YOLOv11s")
    axes[0, 0].set_title("Tong training loss")
    axes[0, 0].set_xlabel("Epoch")
    axes[0, 0].set_ylabel("Box + cls + DFL loss")
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].legend()

    axes[0, 1].plot(yolo8_df["epoch"], yolo8_df["precision"], label="YOLOv8s")
    axes[0, 1].plot(yolo11_df["epoch"], yolo11_df["precision"], label="YOLOv11s")
    axes[0, 1].set_title("Precision")
    axes[0, 1].set_xlabel("Epoch")
    axes[0, 1].set_ylabel("Precision")
    axes[0, 1].set_ylim(0, 1.05)
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].legend()

    axes[1, 0].plot(yolo8_df["epoch"], yolo8_df["recall"], label="YOLOv8s")
    axes[1, 0].plot(yolo11_df["epoch"], yolo11_df["recall"], label="YOLOv11s")
    axes[1, 0].set_title("Recall")
    axes[1, 0].set_xlabel("Epoch")
    axes[1, 0].set_ylabel("Recall")
    axes[1, 0].set_ylim(0, 1.05)
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].legend()

    axes[1, 1].plot(yolo8_df["epoch"], yolo8_df["map50"], label="YOLOv8s mAP@0.5")
    axes[1, 1].plot(yolo11_df["epoch"], yolo11_df["map50"], label="YOLOv11s mAP@0.5")
    axes[1, 1].plot(yolo8_df["epoch"], yolo8_df["map50_95"], "--", label="YOLOv8s mAP@0.5:0.95")
    axes[1, 1].plot(yolo11_df["epoch"], yolo11_df["map50_95"], "--", label="YOLOv11s mAP@0.5:0.95")
    axes[1, 1].set_title("mAP")
    axes[1, 1].set_xlabel("Epoch")
    axes[1, 1].set_ylabel("mAP")
    axes[1, 1].set_ylim(0, 1.05)
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].legend()

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()


plot_compare_yolo_training(yolo8_df, yolo11_df, "compare_yolov8s_yolov11s_training_curves.png")
```

## 6. Code ve bang cot ket qua test set

```python
test_metrics = pd.DataFrame(
    [
        {"model": "YOLOv8s", "precision": 0.963, "recall": 0.926, "map50": 0.973, "map50_95": 0.728},
        {"model": "YOLOv11s", "precision": 0.930, "recall": 0.903, "map50": 0.956, "map50_95": 0.675},
    ]
)

ax = test_metrics.set_index("model").plot(kind="bar", figsize=(9, 5), rot=0)
ax.set_title("So sanh ket qua danh gia tren tap test")
ax.set_ylabel("Gia tri")
ax.set_ylim(0, 1.05)
ax.grid(axis="y", alpha=0.3)
ax.legend(["Precision", "Recall", "mAP@0.5", "mAP@0.5:0.95"])

plt.tight_layout()
plt.savefig("yolo_test_metrics_comparison.png", dpi=300, bbox_inches="tight")
plt.show()
```

## 7. Code xuat mang ra CSV neu can chen vao bao cao

```python
yolo8_df.to_csv("yolov8s_training_metrics_from_notebook.csv", index=False)
yolo11_df.to_csv("yolov11s_training_metrics_from_notebook.csv", index=False)
test_metrics.to_csv("yolo_test_metrics_summary.csv", index=False)
```

