# Báo cáo quá trình train và cải tiến các phiên bản mô hình

## 1. Phạm vi phân tích

Báo cáo này phân loại các notebook trong thư mục `train files/` dựa trên code, cấu hình huấn luyện, loss, sampler, callback, checkpoint và output metric đã lưu trong notebook. Tôi không phân loại theo tên file đơn thuần. Các nhóm chính gồm: pipeline dữ liệu HAM10000, CNN baseline, ConvNeXt/ConvNeXtV2, hybrid ConvNeXt + Swin + Attention, YOLO phát hiện vùng tổn thương, và chuỗi hybrid VGG16 + Inception + ViT.

Một lưu ý quan trọng: một số notebook có output test/classification report giống notebook khác, hoặc chỉ chạy một phần epoch. Vì vậy báo cáo tách rõ “ý tưởng/code cải tiến” và “bằng chứng metric trong output”. Với HAM10000, macro-F1/balanced accuracy thường thuyết phục hơn accuracy thuần vì lớp `nv` chiếm áp đảo, còn các lớp hiếm như `df`, `vasc`, `akiec` dễ bị bỏ qua.

## 2. Pipeline dữ liệu và chuẩn hóa đầu vào

### 2.1 `HAM10000_download.ipynb`

Notebook tải HAM10000 từ Kaggle, giải nén vào Google Drive, đọc `HAM10000_metadata.csv`, thống kê phân bố lớp, giới tính, tuổi và hiển thị ảnh mẫu. Đây là bước nền để chứng minh dữ liệu gốc gồm 7 lớp bệnh da và có mất cân bằng mạnh.

Ưu điểm: có kiểm tra tồn tại dataset, thống kê phân bố lớp và trực quan hóa. Hạn chế: chủ yếu là notebook chuẩn bị dữ liệu, chưa tạo split tái lập cho train/test.

### 2.2 `data_processing.ipynb`

Notebook tạo cột `label` bằng `LabelEncoder`, lưu `class_names.npy`, tìm đường dẫn ảnh trong hai thư mục `HAM10000_images_part_1` và `HAM10000_images_part_2`, loại ảnh thiếu, sau đó chia stratified train/val/test theo tỷ lệ 70/15/15 với `random_state=42`.

Đây là bước rất quan trọng vì mọi notebook phân loại tốt nên dùng cùng split này để so sánh công bằng. Stratified split giúp các lớp hiếm vẫn xuất hiện trong validation/test, tránh metric bị may rủi.

### 2.3 `organize_images_to_classes.ipynb`

Notebook copy ảnh gốc vào thư mục theo class đầy đủ, ví dụ `Basal_cell_carcinoma`, `Melanoma`, `Vascular_lesions`, và có chức năng lấy mẫu ngẫu nhiên 50 ảnh mỗi lớp để zip. Vai trò chính là kiểm tra dữ liệu, demo trực quan, hoặc phục vụ các công cụ cần cấu trúc folder/class.

### 2.4 `yolo_dataset_labeling.ipynb`

Notebook này không phải phân loại HAM10000 mà chuyển ISIC 2018 segmentation mask thành bounding box YOLO. Code đọc mask grayscale, threshold nhị phân, lấy contour lớn nhất, tính bbox normalized `(x_center, y_center, width, height)`, chia train/val/test 70/15/15 và tạo `images/` + `labels/` theo format YOLO một lớp `lesion`.

Ý nghĩa: đây là pipeline detection/segmentation-to-detection, dùng để phát hiện vị trí tổn thương trước hoặc song song với phân loại bệnh. Không nên so sánh trực tiếp accuracy/F1 với classifier HAM10000, vì bài toán và dataset khác nhau.

## 3. Phân loại các mô hình đã train

| Nhóm | Notebook | Bài toán | Kiến trúc/code chính | Mất cân bằng lớp | Bằng chứng metric nổi bật |
|---|---|---|---|---|---|
| CNN baseline PyTorch | `CNN_model_v1.ipynb` | Phân loại 7 lớp HAM10000 | 4 block Conv2D 16/32/64/128 + MaxPool + MLP 64/32 | class weight đã smooth, augment nhẹ | best val_f1 khoảng 0.572, test accuracy khoảng 0.75, macro-F1 khoảng 0.51 |
| CNN baseline Keras | `CNN_model_v2.ipynb` | Phân loại 7 lớp HAM10000 | Conv2D 32/64/128 + Flatten + Dense 256 + Dropout 0.5 + Softmax | class_weight sqrt smoothing, callback macro precision/recall/F1 | test acc khoảng 0.746, macro-F1 khoảng 0.49 |
| ConvNeXtV2 | `ConvNeXtV2.ipynb` | Phân loại 7 lớp HAM10000 | `timm.create_model('convnextv2_tiny', pretrained=True)` | WeightedRandomSampler + CrossEntropy weighted | best val F1 khoảng 0.7849 tại epoch 18 |
| ConvNeXt + Swin + Attention | `ConvNeXt_Swin_Attention.ipynb` | Phân loại + feature extractor | ConvNeXt branch + Swin branch, concat feature map, channel/spatial attention, classifier | class_weight trong training, thử classifier cổ điển trên deep features | train/val deep model best val_acc khoảng 0.8795; classifier MLP trên feature test acc khoảng 0.8024; nhưng có cell eval sau bị sai/lệch checkpoint cho accuracy 0.11 |
| Hybrid VGG16 + Inception + ViT gốc | `VGG16+Inception+ViT.ipynb`, bản sao | Phân loại 7 lớp HAM10000 | VGG16 block feature + InceptionV7 + reducer + patch encoder + transformer + attention pooling | class_weight, label smoothing, 2 phase freeze/unfreeze | best val_acc/F1 khoảng 0.884/0.788, test acc/F1 khoảng 0.876/0.749 |
| Hybrid VGG16 + Inception + ViT v2 | `VGG16+Inception+ViT_v2.ipynb` | Phân loại 7 lớp HAM10000 | Cùng họ hybrid nhưng cấu hình/chuỗi chạy kém ổn định | class_weight | output train chỉ đạt best val_acc/F1 khoảng 0.540/0.505; output test lại giống bản gốc nên cần coi là không độc lập |
| Hybrid v3 | `VGG16+Inception+ViT_v3.ipynb` | Phân loại 7 lớp HAM10000 | Thêm FocalLoss alpha theo class weight, rare augmentation, label smoothing giảm | FocalLoss gamma=2, weight cho lớp hiếm | best val F1 khoảng 0.793; test acc/F1 khoảng 0.848/0.725 |
| Hybrid v4 | `VGG16+Inception+ViT_v4.ipynb` | Phân loại 7 lớp HAM10000 | Staged unfreezing + discriminative LR + FocalLoss | ưu tiên checkpoint theo macro-F1; rare aug | test macro-F1 khoảng 0.76, accuracy 0.87; cải thiện recall lớp hiếm tốt hơn bản gốc |
| Hybrid v5 | `VGG16+Inception+ViT_v5.ipynb` | Phân loại 7 lớp HAM10000 | Code gần v4, staged training + resume/fine-tune | FocalLoss + staged unfreezing | output có phần giống v3 và phần train staged thấp hơn; cần coi là bản thử nghiệm/resume chưa sạch |
| CB-Focal hybrid | `train_vgg_inception_vit_cbfocal.ipynb` | Phân loại 7 lớp HAM10000 | Refactor có `CFG` dataclass, WeightedRandomSampler, CBFocalLoss | Class-Balanced Focal Loss beta=0.9999 + sampler | mới thấy Phase 1 tới epoch 4: val_acc 0.1684, F1 0.2786, balanced acc 0.5857; chưa đủ kết luận |
| YOLOv8s | `yolo8s_focalloss.ipynb` | Detection lesion 1 lớp | Ultralytics YOLOv8s, imgsz 640, AdamW, cosine LR, augment lesion | không phải class imbalance 7 lớp; một class bbox | val mAP50 0.982, test mAP50 0.973, test mAP50-95 0.728 |
| YOLO11s | `yolo11s_focalloss.ipynb` | Detection lesion 1 lớp | Ultralytics YOLO11s, config gần YOLOv8s | một class bbox | val mAP50 0.974, test mAP50 0.956, test mAP50-95 0.675 |

## 4. Diễn tiến cải tiến theo từng họ mô hình

### 4.1 CNN v1 -> CNN v2: baseline nhanh để hiểu dữ liệu

`CNN_model_v1.ipynb` dùng PyTorch custom CNN gồm 4 block convolution 3x3, số kênh 16 -> 32 -> 64 -> 128, mỗi block có ReLU và MaxPool. Với input 224x224, feature map xuống 14x14x128 rồi Flatten vào MLP 64 -> 32 -> 7. Đây là baseline dễ giải thích, số tầng ít, phù hợp để kiểm tra pipeline, augmentation và class imbalance.

`CNN_model_v2.ipynb` chuyển sang Keras lightweight CNN: Conv2D 32/64/128, Flatten, Dense 256, Dropout 0.5 và Softmax. Điểm cải tiến nằm ở workflow rõ hơn: `ImageDataGenerator`, class_weight có smoothing sqrt, callback tự tính macro precision/recall/F1, checkpoint `.keras`, EarlyStopping và ReduceLROnPlateau.

Kết luận cho họ CNN: hai bản này tốt để làm baseline và giải thích trong báo cáo, nhưng không phải lựa chọn thuyết phục nhất nếu mục tiêu là hiệu năng. Macro-F1 quanh 0.49-0.51 cho thấy mô hình vẫn yếu ở lớp hiếm, đặc biệt `df` và `mel`.

### 4.2 ConvNeXtV2: backbone hiện đại, mạnh và gọn hơn hybrid phức tạp

`ConvNeXtV2.ipynb` dùng `timm.create_model('convnextv2_tiny', pretrained=True, num_classes=7)`. Code có `WeightedRandomSampler` theo nghịch đảo class count, CrossEntropyLoss có `class_weights_tensor`, AdamW lr=1e-4, weight_decay=1e-5 và CosineAnnealingLR.

Điểm mạnh là dùng pretrained backbone hiện đại với inductive bias CNN tốt cho ảnh y khoa, trong khi code tương đối gọn. Best validation F1 khoảng 0.7849 tại epoch 18, ngang hoặc gần các biến thể hybrid tốt nhất. Nếu cần mô hình thuyết phục theo cân bằng giữa hiệu năng, độ sạch code và khả năng bảo trì, ConvNeXtV2 là ứng viên rất mạnh.

Rủi ro: augment có `RandomVerticalFlip(p=0.5)`. Với ảnh tổn thương da, vertical flip không nghiêm trọng như ảnh X-quang có hướng giải phẫu, nhưng vẫn nên biện luận hoặc giảm nếu muốn pipeline thận trọng hơn.

### 4.3 ConvNeXt + Swin + Attention: ý tưởng mạnh nhưng cần kiểm soát đánh giá

`ConvNeXt_Swin_Attention.ipynb` xây mô hình hai nhánh: ConvNeXt trích đặc trưng cục bộ và Swin Transformer trích đặc trưng cửa sổ/hình thái; sau đó project bằng 1x1 conv, concat channel, qua ChannelAttention và SpatialAttention rồi classifier. Code còn thêm hướng “paper-style protocol”: lấy deep features rồi train SVM, KNN, Logistic Regression, Decision Tree và MLP.

Trong training chính, best validation accuracy đạt khoảng 0.8795. Khi dùng deep features cho classifier cổ điển, MLP đạt test accuracy khoảng 0.8024, SVM_RBF khoảng 0.7505. Tuy nhiên cell đánh giá cuối in classification report accuracy 0.11 và dự đoán gần như dồn vào `bkl`, đây có khả năng là do load/evaluate sai checkpoint, sai trạng thái model, hoặc feature head không khớp với mô hình tốt nhất.

Kết luận: kiến trúc rất đáng trình bày như hướng nghiên cứu, nhưng hiện tại bằng chứng chưa sạch bằng ConvNeXtV2 hoặc hybrid v4. Nếu chọn mô hình này, cần chạy lại evaluation từ checkpoint tốt nhất và báo cáo macro-F1, confusion matrix chuẩn.

### 4.4 VGG16 + Inception + ViT bản gốc: hybrid có kết quả mạnh

`VGG16+Inception+ViT.ipynb` và `Bản sao của VGG16+Inception+ViT.ipynb` có cùng cấu trúc code/output. Kiến trúc gồm VGG16 blocks lấy feature pretrained, InceptionV7 mở rộng receptive field đa nhánh, SpatialReducer giảm kích thước, PatchEncoder đưa feature map thành token, ViTEncoder xử lý quan hệ toàn cục, AttentionPool gom token trước classifier.

Cấu hình chính: img_size 224, epochsA=15, epochsB=40, phase A train head với lr 4e-4, phase B unfreeze backbone lr 2e-5 và head lr 6e-5, AdamW, cosine warmup, grad clipping, AMP, CrossEntropyLoss label_smoothing=0.1.

Bản này có bằng chứng tốt: best validation accuracy/F1 khoảng 0.884/0.788; test accuracy/F1 khoảng 0.876/0.749; classification report test có macro avg precision/recall/F1 khoảng 0.78/0.73/0.75. Ưu điểm là accuracy cao và weighted F1 tốt; hạn chế là vẫn có lớp `df` recall thấp 0.41 và `mel` recall 0.57.

### 4.5 v2: thử nghiệm bị mất ổn định

`VGG16+Inception+ViT_v2.ipynb` vẫn thuộc họ hybrid nhưng output training cho thấy Phase B best validation accuracy/F1 chỉ khoảng 0.540/0.505, thấp hơn nhiều bản gốc. Đáng chú ý, phần test output lại giống bản gốc 0.876/0.749, nên nhiều khả năng cell test đã load checkpoint cũ hoặc notebook chưa được chạy lại sạch từ đầu.

Kết luận: không nên dùng v2 làm bằng chứng chính. Nó nên được ghi là thử nghiệm không ổn định, hữu ích để chứng minh quá trình tìm kiếm cấu hình nhưng không đủ thuyết phục để chọn.

### 4.6 v3: chuyển trọng tâm từ accuracy sang lớp hiếm bằng FocalLoss

`VGG16+Inception+ViT_v3.ipynb` thêm `FocalLoss` với gamma=2.0, alpha theo class weight, `rare_aug_prob=0.75`, giảm label_smoothing từ 0.1 xuống 0.05. Về mặt tư duy, đây là cải tiến đúng hướng cho HAM10000 vì accuracy cao có thể bị lớp `nv` kéo lên.

Best validation F1 đạt khoảng 0.793, nhỉnh hơn bản gốc. Test accuracy/F1 khoảng 0.848/0.725; macro avg precision/recall/F1 khoảng 0.80/0.69/0.73. So với bản gốc, v3 cải thiện precision macro nhưng recall macro thấp hơn, đặc biệt `vasc` recall 0.59 và `df` recall 0.41. Điều này cho thấy FocalLoss giúp tập trung mẫu khó nhưng chưa tự động giải quyết hết recall lớp hiếm.

### 4.7 v4: phiên bản thuyết phục nhất trong họ hybrid

`VGG16+Inception+ViT_v4.ipynb` là cải tiến có chủ đích nhất. Code thêm staged unfreezing và discriminative learning rate:

- Stage 1 chỉ train `attn_pool`, `norm`, `classifier`.
- Stage 2 mở `patch_encoder`, `transformer`.
- Stage 3 mở `inception`, `reducer`.
- Stage 4 fine-tune toàn bộ, nhưng VGG dùng LR rất nhỏ.

Ngoài ra, v4 chọn checkpoint ưu tiên macro-F1, nếu hòa mới xét accuracy. Đây là quyết định hợp lý nhất cho dữ liệu lệch lớp. Best validation F1 khoảng 0.779, best validation accuracy khoảng 0.871; test accuracy/F1 khoảng 0.870/0.764. Classification report test có macro precision/recall/F1 khoảng 0.79/0.75/0.76.

Điểm đáng giá nhất: recall các lớp hiếm cải thiện rõ hơn bản gốc: `df` recall từ 0.41 lên 0.59, `vasc` từ 0.82 xuống 0.73 nhưng vẫn tốt, `akiec` 0.76, `bcc` 0.82. Nếu mục tiêu là báo cáo khoa học về phân loại bệnh da, v4 thuyết phục hơn bản gốc vì không chỉ tối ưu lớp đa số.

### 4.8 v5: bản resume/thử nghiệm cần làm sạch trước khi trích dẫn

`VGG16+Inception+ViT_v5.ipynb` có code gần v4: staged training, FocalLoss, resume checkpoint, fine-tune thêm. Tuy nhiên output bị lẫn: phần staged `S4_full` best F1 khoảng 0.700, phần test report lại giống v3 với test acc/F1 0.848/0.725. Điều này cho thấy notebook chưa phải bằng chứng độc lập sạch.

Kết luận: v5 nên được xem là bản thử nghiệm resume/fine-tune, không nên chọn làm mô hình chính nếu chưa chạy lại từ đầu và lưu checkpoint/result riêng.

### 4.9 `train_vgg_inception_vit_cbfocal.ipynb`: refactor tốt, nhưng metric chưa đủ

Notebook này đáng chú ý vì refactor chuyên nghiệp hơn: dùng `dataclass CFG`, resolve path rõ, `WeightedRandomSampler`, transform riêng train/eval, `CBFocalLoss` dựa trên effective number of samples với beta=0.9999 và gamma=2.0, đồng thời log balanced accuracy.

Ý tưởng Class-Balanced Focal Loss rất phù hợp với HAM10000. Tuy nhiên output hiện mới thấy Phase 1 tới epoch 4: val accuracy 0.1684, F1 0.2786, balanced accuracy 0.5857. Accuracy thấp có thể do sampler/loss làm phân phối dự đoán cân bằng hơn ở giai đoạn đầu, nhưng chưa đủ epoch để kết luận. Đây là hướng nên tiếp tục train, không phải mô hình đã chứng minh tốt nhất.

### 4.10 YOLOv8s và YOLO11s: mô hình phát hiện vùng tổn thương, không phải classifier 7 lớp

Hai notebook YOLO dùng dataset ISIC segmentation đã chuyển sang bbox một lớp `lesion`. Cấu hình train gần giống nhau: 100 epoch, imgsz=640, auto batch, AdamW, lr0=0.01, cosine LR, patience=30, augment phù hợp ảnh da như degrees=5, translate=0.1, scale=0.15, fliplr=0.5, mosaic=0.5, mixup=0.1, copy_paste=0.1, close_mosaic=10.

Kết quả YOLOv8s tốt hơn YOLO11s trong output lưu lại: YOLOv8s test precision/recall/mAP50/mAP50-95 khoảng 0.963/0.926/0.973/0.728; YOLO11s khoảng 0.930/0.903/0.956/0.675. Nếu mục tiêu là định vị lesion trước khi crop rồi phân loại, YOLOv8s là lựa chọn detection thuyết phục hơn trong các notebook hiện có.

## 5. So sánh ưu điểm và cách chọn mô hình

| Mục tiêu chọn mô hình | Nên chọn | Lý do |
|---|---|---|
| Baseline dễ giải thích | CNN v1 hoặc CNN v2 | Kiến trúc ngắn, dễ mô tả, chứng minh pipeline hoạt động |
| Hiệu năng phân loại tốt nhưng code gọn | ConvNeXtV2 | Pretrained backbone mạnh, best val F1 khoảng 0.785, ít thành phần tự chế |
| Báo cáo hybrid sáng tạo | VGG16+Inception+ViT v4 | Có logic cải tiến rõ: focal loss, rare augmentation, staged unfreezing, macro-F1 checkpoint |
| Tối ưu accuracy/weighted performance | VGG16+Inception+ViT bản gốc | Test accuracy khoảng 0.876, weighted avg F1 khoảng 0.87 |
| Tối ưu thuyết phục với dữ liệu lệch lớp | VGG16+Inception+ViT v4 | Macro-F1 test khoảng 0.76, recall lớp hiếm tốt hơn bản gốc |
| Phát hiện/crop lesion trước phân loại | YOLOv8s | Test mAP50 khoảng 0.973, mAP50-95 khoảng 0.728 |
| Hướng nghiên cứu feature fusion | ConvNeXt + Swin + Attention | Ý tưởng hai nhánh + attention tốt, nhưng cần đánh giá lại checkpoint sạch |
| Hướng tiếp tục cải tiến loss imbalance | CB-Focal hybrid | Code loss/sampler hợp lý nhưng cần train đủ epoch |

## 6. Nhận định mô hình thuyết phục nhất

Nếu cần chọn một mô hình phân loại chính cho báo cáo, tôi đề xuất `VGG16+Inception+ViT_v4.ipynb`. Lý do không chỉ vì metric cao, mà vì quá trình cải tiến có luận cứ kỹ thuật rõ ràng: chuyển từ train 2 phase sang staged unfreezing, dùng LR phân tầng theo module, dùng FocalLoss cho mất cân bằng lớp, ưu tiên macro-F1 khi lưu checkpoint, và kiểm soát fine-tune VGG bằng LR nhỏ.

Nếu hội đồng hoặc người đọc ưu tiên đơn giản và reproducibility, `ConvNeXtV2.ipynb` là lựa chọn dự phòng rất mạnh. Nó có ít thành phần tự chế hơn, dễ chạy lại, và metric validation F1 cạnh tranh. Có thể trình bày ConvNeXtV2 như baseline pretrained hiện đại, còn VGG16+Inception+ViT v4 như mô hình đề xuất/cải tiến.

Với detection, `yolo8s_focalloss.ipynb` là lựa chọn tốt hơn `yolo11s_focalloss.ipynb` theo output hiện có. Tuy nhiên nó giải quyết bài toán khác: phát hiện bbox lesion, không phân loại 7 bệnh. Cách dùng hợp lý là pipeline hai bước: YOLOv8s crop/định vị vùng tổn thương, sau đó classifier như ConvNeXtV2 hoặc hybrid v4 phân loại bệnh.

## 7. Các điểm cần làm trước khi chốt báo cáo cuối

1. Chạy lại sạch các notebook ứng viên từ đầu với cùng split `train_split.csv`, `val_split.csv`, `test_split.csv`.
2. Lưu riêng checkpoint/result theo version để tránh v2/v5 load nhầm checkpoint của bản khác.
3. Báo cáo cùng bộ metric: accuracy, macro-F1, weighted-F1, balanced accuracy, confusion matrix và per-class recall.
4. Với HAM10000, đặt macro-F1 và recall lớp hiếm là tiêu chí chính; accuracy chỉ là tiêu chí phụ.
5. Với ConvNeXt + Swin + Attention, cần sửa/kiểm tra cell evaluation vì output cuối không khớp với training tốt nhất.
6. Với CB-Focal hybrid, cần train đủ phase và so sánh với v4 trên cùng test set trước khi kết luận.

## 8. Kết luận ngắn

Quá trình train thể hiện một lộ trình hợp lý: bắt đầu bằng CNN baseline để kiểm tra dữ liệu, chuyển sang pretrained backbone như ConvNeXtV2 để tăng năng lực biểu diễn, thử fusion ConvNeXt/Swin và hybrid VGG16+Inception+ViT để kết hợp đặc trưng cục bộ/toàn cục, sau đó cải tiến loss và chiến lược fine-tune để xử lý mất cân bằng lớp. Trong trạng thái notebook hiện tại, bản hybrid v4 là ứng viên phân loại thuyết phục nhất về mặt luận cứ kỹ thuật, ConvNeXtV2 là ứng viên gọn và dễ bảo trì nhất, còn YOLOv8s là mô hình tốt nhất cho nhánh phát hiện lesion.
