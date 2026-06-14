# CHƯƠNG 2: CƠ SỞ LÝ THUYẾT

## 2.1. Bài toán hỗ trợ chẩn đoán bệnh da liễu từ ảnh

### 2.1.1. Đặc điểm ảnh tổn thương da

Ảnh tổn thương da là nguồn dữ liệu trực quan quan trọng trong khám da liễu. Một ảnh có thể chứa nhiều dấu hiệu liên quan đến chẩn đoán như màu sắc, bờ tổn thương, hình dạng tổng thể, cấu trúc sắc tố, vùng loét, mạch máu và mức độ không đồng nhất của bề mặt. Một số dấu hiệu nằm ở vùng rất nhỏ, chẳng hạn chấm sắc tố hoặc đường viền bất thường, trong khi một số dấu hiệu khác cần quan sát toàn bộ vùng tổn thương, chẳng hạn sự bất đối xứng hoặc phân bố màu không đều. Vì vậy, bài toán phân tích ảnh da liễu cần mô hình có khả năng học cả đặc trưng cục bộ và đặc trưng toàn cục.

Trong phạm vi đồ án, hệ thống không đưa ra chẩn đoán y khoa cuối cùng. Mục tiêu là hỗ trợ phân tích ảnh, phát hiện vùng tổn thương, phân loại nhóm bệnh tham khảo và sinh phản hồi giải thích bằng tiếng Việt. Điều này phù hợp với bản chất của ứng dụng hỗ trợ: mô hình học máy cung cấp thông tin ban đầu, còn quyết định y khoa vẫn cần bác sĩ da liễu xác nhận.

### 2.1.2. Pipeline tổng quát của đề tài

Pipeline của đồ án gồm các bước chính: ảnh đầu vào, kiểm tra ảnh da, phát hiện vùng tổn thương bằng YOLO, phân loại bằng mô hình lai VGG16, Inception và Vision Transformer, sau đó đưa tên bệnh cùng câu hỏi của người dùng vào pipeline truy xuất tăng cường sinh văn bản để tạo phản hồi. Việc tổ chức pipeline nhiều bước giúp hệ thống giảm rủi ro ở từng giai đoạn. Nếu ảnh không phải ảnh da, hệ thống dừng sớm. Nếu ảnh hợp lệ, YOLO xác định vùng tổn thương để mô hình phân loại tập trung vào vùng có ý nghĩa. Sau khi có kết quả phân loại, RAG bổ sung ngữ cảnh y khoa để câu trả lời không chỉ là một nhãn bệnh rời rạc.

Hình 2.1 Pipeline tổng thể của hệ thống hỗ trợ chẩn đoán bệnh da liễu

> Chèn hình pipeline tổng thể: Input Image -> Skin Detection Module -> YOLO Detection -> Crop Diseased Region -> CNN Classifier -> RAG Pipeline -> Generated Response.

## 2.2. Dữ liệu sử dụng trong đề tài

### 2.2.1. Bộ dữ liệu HAM10000 cho phân loại bệnh

HAM10000 là bộ dữ liệu gồm 10015 ảnh soi da của các tổn thương sắc tố thường gặp. Theo paper gốc, bộ dữ liệu được thu thập từ nhiều nguồn, nhiều quần thể và nhiều thiết bị khác nhau, nhờ đó tăng độ đa dạng so với các bộ dữ liệu nhỏ trước đây [1]. Trong bài báo, nhóm tác giả mô tả bộ dữ liệu bằng đoạn trích: "final dataset consists of 10015 dermatoscopic images" [1]. Đồ án sử dụng HAM10000 cho bài toán phân loại bảy lớp bệnh, không dùng bộ này để huấn luyện YOLO.

Bảng 2.1 Các lớp bệnh trong phạm vi đồ án

| Mã lớp | Tên tiếng Anh | Diễn giải tiếng Việt |
|---|---|---|
| `akiec` | Actinic keratosis / Bowen's disease | Dày sừng ánh sáng hoặc bệnh Bowen, có liên quan tổn thương tiền ung thư |
| `bcc` | Basal cell carcinoma | Ung thư biểu mô tế bào đáy |
| `bkl` | Benign keratosis | Nhóm dày sừng lành tính, gồm seborrheic keratosis và solar lentigo |
| `df` | Dermatofibroma | U xơ bì, thường lành tính |
| `mel` | Melanoma | Ung thư hắc tố, nhóm nguy hiểm cần phát hiện sớm |
| `nv` | Melanocytic nevus | Nốt ruồi sắc tố, thường lành tính |
| `vasc` | Vascular lesion | Tổn thương mạch máu như hemangioma hoặc angiokeratoma |

HAM10000 có hiện tượng mất cân bằng dữ liệu. Lớp melanocytic nevus chiếm tỷ lệ lớn, trong khi dermatofibroma hoặc vascular lesion có số lượng ít hơn nhiều. Vì vậy, accuracy không đủ để đánh giá toàn diện mô hình. Khi báo cáo kết quả phân loại, cần bổ sung precision, recall, F1-score theo từng lớp và ma trận nhầm lẫn để xem mô hình có bỏ sót lớp hiếm hay không.

### 2.2.2. Bộ dữ liệu ISIC 2018 Task 1 cho huấn luyện YOLO

YOLO trong đồ án không được huấn luyện trên HAM10000. Theo notebook `yolo_dataset_labeling.ipynb`, dữ liệu YOLO được lấy từ ISIC 2018 Challenge Task 1: Lesion Boundary Segmentation. Bộ dữ liệu này cung cấp ảnh tổn thương da và mask ground truth tương ứng, phù hợp cho việc tạo bounding box huấn luyện detector. Trang ISIC Challenge mô tả rằng ground truth dùng cho huấn luyện được tạo bằng nhiều kỹ thuật và được rà soát bởi bác sĩ da liễu có chuyên môn soi da [15]. Paper tổng kết ISIC 2018 cũng cho biết challenge gồm hơn 12.500 ảnh qua ba tác vụ: segmentation, attribute detection và disease classification [16].

Trong notebook, ảnh gốc được lấy từ thư mục `ISIC2018_Task1-2_Training_Input`, mask lấy từ `ISIC2018_Task1_Training_GroundTruth`. Với mỗi ảnh, mask `_segmentation.png` được nhị phân hóa, tìm contour ngoài lớn nhất, sau đó dùng `cv2.boundingRect` để lấy bounding box bao quanh vùng tổn thương. Nhãn YOLO được lưu theo một lớp duy nhất là `lesion`.

Công thức chuyển từ bounding box pixel sang nhãn YOLO như sau. Gọi kích thước ảnh là W x H, bounding box có góc trái trên là (x, y), chiều rộng w và chiều cao h. Khi đó:

`x_center = (x + w / 2) / W`

`y_center = (y + h / 2) / H`

`width = w / W`

`height = h / H`

Mỗi file nhãn có dạng: `0 x_center y_center width height`. Trong đó `0` là mã lớp lesion. Notebook chia dữ liệu thành train, validation và test theo tỷ lệ 70%, 15%, 15% bằng `train_test_split`, sau đó lưu theo cấu trúc chuẩn YOLO: `images/train`, `images/val`, `images/test`, `labels/train`, `labels/val`, `labels/test`.

Hình 2.2 Minh họa chuyển mask phân đoạn ISIC 2018 thành bounding box YOLO

> Chèn hình gồm ba phần: ảnh gốc, mask ground truth, bounding box tạo từ contour lớn nhất.

### 2.2.3. Vấn đề mất cân bằng dữ liệu và chỉ số đánh giá

Với bài toán phân loại bệnh, mất cân bằng lớp có thể khiến mô hình thiên về lớp xuất hiện nhiều. Vì vậy, bên cạnh accuracy, báo cáo cần dùng macro precision, macro recall và macro F1-score. Precision phản ánh mức độ dự đoán đúng trong các mẫu được gán vào một lớp; recall phản ánh khả năng tìm đủ mẫu thật của lớp đó; F1-score cân bằng giữa precision và recall. Với bài toán phát hiện vùng tổn thương, cần dùng precision, recall và mean Average Precision dựa trên ngưỡng IoU.

## 2.3. Cơ sở lý thuyết mạng tích chập

### 2.3.1. Phép tích chập, hàm kích hoạt và pooling

Mạng tích chập là nền tảng của nhiều mô hình thị giác máy tính. Với ảnh đầu vào X, bộ lọc W và bias b, phép tích chập tại vị trí (i, j) của kênh đầu ra k có thể viết:

`Y(i, j, k) = b_k + Σ_c Σ_u Σ_v W(u, v, c, k) . X(i + u, j + v, c)`

Công thức trên cho thấy mỗi bộ lọc học một mẫu đặc trưng cục bộ trên ảnh, chẳng hạn cạnh, màu, cấu trúc sắc tố hoặc vùng chuyển tiếp. Sau tích chập, mô hình thường dùng hàm kích hoạt phi tuyến. Hàm ReLU được dùng phổ biến:

`ReLU(x) = max(0, x)`

Pooling giúp giảm kích thước không gian của feature map, giảm chi phí tính toán và tăng tính ổn định trước những thay đổi nhỏ trong ảnh. Ở tầng cuối, mô hình phân loại thường dùng softmax để chuyển logits z thành xác suất:

`p_i = exp(z_i) / Σ_j exp(z_j)`

Hàm mất mát phân loại phổ biến là cross-entropy:

`L = - Σ_i y_i log(p_i)`

Trong đó y_i là nhãn thật ở dạng one-hot và p_i là xác suất dự đoán của lớp i.

Hình 2.3 Phép tích chập trong mạng CNN

> Chèn hình minh họa phép tích chập: ảnh đầu vào, kernel trượt và feature map đầu ra.

### 2.3.2. VGG16

VGG16 là một kiến trúc mạng tích chập kinh điển, nổi bật nhờ việc sử dụng nhiều bộ lọc nhỏ 3 x 3 và tăng chiều sâu mạng một cách có hệ thống. Simonyan và Zisserman cho thấy việc tăng độ sâu lên “16-19 weight layers” giúp cải thiện hiệu quả phân loại ảnh [4]. Thiết kế của VGG đơn giản: nhiều lớp tích chập 3 x 3 được xếp liên tiếp, sau đó là pooling và các lớp fully connected. Nhờ cấu trúc rõ ràng, VGG16 thường được dùng làm backbone hoặc bộ trích xuất đặc trưng trong nhiều bài toán ảnh y tế.

Trong đồ án, VGG16 không được dùng như một classifier độc lập. Mô hình chỉ sử dụng phần block tích chập của VGG16 để trích xuất đặc trưng ban đầu, sau đó đặc trưng được đưa qua Inception và Vision Transformer. Cách dùng này tận dụng khả năng học đặc trưng cục bộ của VGG16 nhưng tránh phụ thuộc hoàn toàn vào một mạng VGG đầy đủ nhiều tham số.

Hình 2.4 Kiến trúc VGG16 trong paper “Very Deep Convolutional Networks for Large-Scale Image Recognition”

> Chèn hình kiến trúc VGG16 từ paper VGG [4].

### 2.3.3. Inception

Inception được giới thiệu trong paper “Going Deeper with Convolutions”. Ý tưởng chính là xử lý cùng một đầu vào qua nhiều nhánh song song, chẳng hạn tích chập 1 x 1, 3 x 3, 5 x 5 và pooling, sau đó ghép các đầu ra theo chiều kênh [14]. Cấu trúc này giúp mô hình học đặc trưng ở nhiều tỷ lệ khác nhau. Paper Inception cũng nhấn mạnh vai trò của tích chập 1 x 1 trong việc giảm số kênh trước các phép tích chập lớn, nhờ đó giảm chi phí tính toán.

Với ảnh tổn thương da, đặc trưng quan trọng có thể xuất hiện ở nhiều kích thước: vùng đổi màu lớn, bờ tổn thương, chấm sắc tố nhỏ hoặc cấu trúc mạch máu. Vì vậy, ý tưởng đặc trưng đa tỷ lệ của Inception phù hợp với bài toán. Trong mô hình của đồ án, InceptionV7 được đặt sau VGG16 để làm giàu feature map trước khi đưa sang Transformer.

Hình 2.5 Inception module trong paper “Going Deeper with Convolutions”

> Chèn hình Inception module gốc từ paper GoogLeNet/Inception [14].

## 2.4. Phát hiện vùng tổn thương bằng YOLO

### 2.4.1. Bài toán phát hiện đối tượng

Phát hiện đối tượng là bài toán xác định vị trí và loại đối tượng trong ảnh. Kết quả của detector gồm bounding box, điểm tin cậy và nhãn lớp. Trong đồ án, YOLO chỉ phát hiện một lớp là `lesion`, nghĩa là vùng tổn thương da. Detector không quyết định bệnh cuối cùng, mà cung cấp vùng quan tâm để bước phân loại tập trung vào phần ảnh có ý nghĩa.

Chỉ số quan trọng trong phát hiện đối tượng là Intersection over Union:

`IoU = Area(B_pred ∩ B_gt) / Area(B_pred ∪ B_gt)`

Trong đó B_pred là hộp dự đoán và B_gt là hộp ground truth. IoU càng cao thì hộp dự đoán càng khớp với vùng thật. Khi đánh giá detector, IoU được dùng để xác định một dự đoán có được tính là đúng hay không.

### 2.4.2. Nguyên lý YOLO

YOLO là họ mô hình phát hiện đối tượng một giai đoạn. Thay vì tạo region proposal rồi phân loại từng vùng, YOLO dự đoán trực tiếp bounding box và xác suất lớp từ ảnh đầu vào. Paper YOLO gốc mô tả ý tưởng bằng câu: “single neural network predicts bounding boxes” [2]. Cách tiếp cận này giúp YOLO có tốc độ cao và phù hợp với ứng dụng cần phản hồi nhanh.

YOLO hiện đại thường có ba phần: backbone để trích xuất đặc trưng, neck để kết hợp đặc trưng đa tỷ lệ, và head để dự đoán bounding box. Sau khi sinh nhiều hộp dự đoán, hệ thống dùng Non-Maximum Suppression để loại bỏ các hộp trùng lặp mạnh. Quy tắc thường dùng là giữ hộp có confidence cao nhất và loại các hộp còn lại nếu IoU với hộp đã giữ vượt ngưỡng.

Hình 2.6 Kiến trúc và cơ chế dự đoán của YOLO trong paper “You Only Look Once”

> Chèn hình kiến trúc YOLO hoặc hình chia lưới dự đoán bounding box từ paper YOLO [2].

Công thức 2.1 Hàm mất mát YOLO gốc

> Chèn công thức hàm mất mát YOLO từ paper “You Only Look Once” [2], gồm các thành phần localization loss, confidence loss và classification loss.

### 2.4.3. YOLOv8 và YOLOv11

YOLOv8 là phiên bản do Ultralytics phát triển, hỗ trợ nhiều tác vụ như phát hiện đối tượng, phân đoạn và phân loại. Theo tài liệu Ultralytics, YOLOv8 sử dụng detection head theo hướng anchor-free, giúp giảm phụ thuộc vào anchor box thiết kế thủ công [12]. Trong đồ án, YOLOv8 được triển khai bằng model `yolov8s.pt`.

YOLOv11 là phiên bản mới hơn trong hệ sinh thái Ultralytics. Bài tổng quan YOLOv11 mô tả các thành phần như C3k2, SPPF và C2PSA nhằm tăng khả năng trích xuất đặc trưng và cải thiện hiệu quả tính toán [3]. Tài liệu so sánh của Ultralytics cho biết YOLO11 thay thế một số module C2f bằng C3k2 và bổ sung C2PSA để tăng xử lý đặc trưng không gian [13]. Trong đồ án, YOLOv11 được triển khai bằng model `yolov11s.pt`.

Bảng 2.2 So sánh ngắn gọn YOLOv8 và YOLOv11 trong phạm vi đồ án

| Tiêu chí | YOLOv8 | YOLOv11 |
|---|---|---|
| File model | `backend/models/yolov8s.pt` | `backend/models/yolov11s.pt` |
| Dữ liệu huấn luyện | ISIC 2018 Task 1 được chuyển mask sang bounding box YOLO | ISIC 2018 Task 1 được chuyển mask sang bounding box YOLO |
| Số lớp phát hiện | 1 lớp lesion | 1 lớp lesion |
| Vai trò | Phát hiện vùng tổn thương | Phát hiện vùng tổn thương |

### 2.4.4. Chỉ số đánh giá detector

Khi đánh giá YOLO, các chỉ số cần quan tâm gồm precision, recall và mean Average Precision. Precision phản ánh tỷ lệ dự đoán đúng trong các hộp được mô hình phát hiện. Recall phản ánh tỷ lệ ground truth được mô hình phát hiện. mean Average Precision thường được tính dựa trên đường precision-recall ở các ngưỡng IoU khác nhau. Trong báo cáo thực nghiệm, cần trình bày mAP@0.5 và mAP@0.5:0.95 nếu có kết quả huấn luyện.

Hình 2.7 Ví dụ kết quả phát hiện vùng tổn thương bằng YOLO

> Chèn ảnh minh họa: ảnh da đầu vào, bounding box dự đoán, confidence score.

## 2.5. Mô hình phân loại lai VGG16, Inception và Vision Transformer

### 2.5.1. Thực trạng mô hình phân loại trên HAM10000

Các nghiên cứu trên HAM10000 thường sử dụng VGG, ResNet, Inception, Xception, DenseNet, MobileNet và EfficientNet. Nghiên cứu của Akter và cộng sự đã đánh giá nhiều mô hình trong cùng bài toán phân loại bảy lớp tổn thương da. Theo kết quả công bố, InceptionV3 đạt 90% accuracy, Xception và DenseNet đạt 88%, MobileNet đạt 87%, ResNet đạt 82%, mô hình mạng tích chập tự xây dựng đạt 77% và VGG16 đạt 77% [11]. Kết quả này cho thấy việc chọn mô hình không nên chỉ dựa vào một backbone đơn lẻ, mà cần cân bằng giữa khả năng học đặc trưng, chi phí tính toán và mục tiêu triển khai.

Ảnh da liễu cần nhận biết chi tiết cục bộ như chấm sắc tố, đường viền hoặc cấu trúc nhỏ, đồng thời cần hiểu hình dạng và phân bố màu trên toàn bộ tổn thương. Vì vậy, hướng mô hình lai là hợp lý: mạng tích chập học đặc trưng cục bộ, Inception làm giàu đặc trưng đa tỷ lệ, còn Transformer học quan hệ dài giữa các vùng đặc trưng.

### 2.5.2. Vision Transformer và cơ chế chú ý

Vision Transformer biểu diễn ảnh hoặc feature map thành chuỗi token rồi đưa qua Transformer Encoder. Công thức scaled dot-product attention trong Transformer là:

`Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V`

Cơ chế này giúp mô hình học quan hệ giữa các vùng xa nhau trong ảnh. Với ảnh tổn thương da, self-attention hữu ích vì sự bất thường có thể nằm ở tương quan giữa màu sắc, bờ tổn thương và cấu trúc tổng thể. Tuy nhiên, Vision Transformer thuần thường cần nhiều dữ liệu, nên trong đồ án Transformer được đặt sau phần trích xuất đặc trưng tích chập.

Hình 2.8 Mô hình Vision Transformer trong paper “An Image is Worth 16x16 Words”

> Chèn hình tổng quan Vision Transformer từ paper ViT [5].

### 2.5.3. Mô hình lai tham khảo PlantXViT

Mô hình phân loại trong đồ án được tham khảo từ paper PlantXViT: “Explainable vision transformer enabled convolutional neural network for plant disease identification: PlantXViT” [10]. Đây là mô hình lai gọn nhẹ đã được áp dụng trên bài toán phân loại bệnh cây. Paper này đề xuất kết hợp mạng tích chập với Vision Transformer, có khoảng 0,8 triệu tham số huấn luyện và được thiết kế cho bối cảnh cần hiệu quả tính toán [10].

Trong đồ án, mô hình được điều chỉnh cho bảy lớp bệnh của HAM10000. Kiến trúc gồm VGG16Blocks, InceptionV7, SpatialReducer, PatchEncoder, ViTEncoder, AttentionPool và Linear classifier. VGG16Blocks học đặc trưng cục bộ; InceptionV7 làm giàu đặc trưng đa tỷ lệ; SpatialReducer giảm kích thước feature map; PatchEncoder biến feature map thành token; ViTEncoder học quan hệ giữa các token; AttentionPool tổng hợp đặc trưng; Linear classifier đưa ra tên bệnh và độ tin cậy.

Hình 2.9 Kiến trúc mô hình phân loại lai VGG16, Inception và Vision Transformer

> Chèn hình kiến trúc mô hình: input 224 x 224 x 3 -> VGG16Blocks -> InceptionV7 -> SpatialReducer -> PatchEncoder -> ViTEncoder -> AttentionPool -> Linear classifier.

## 2.6. Truy xuất tăng cường sinh văn bản

### 2.6.1. Khái niệm RAG

Truy xuất tăng cường sinh văn bản là phương pháp kết hợp mô hình ngôn ngữ với kho tri thức bên ngoài. Thay vì chỉ dựa vào kiến thức nằm trong tham số của mô hình, hệ thống truy xuất các đoạn tài liệu liên quan rồi đưa vào prompt để sinh câu trả lời. Lewis và cộng sự mô tả RAG là mô hình “combine pre-trained parametric and non-parametric memory” [6]. Trong miền y tế, cách làm này giúp câu trả lời bám vào nguồn tri thức được kiểm soát hơn.

Paper RAG biểu diễn xác suất sinh câu trả lời y theo đầu vào x bằng cách biên hóa qua các tài liệu truy xuất z. Công thức khái quát có thể viết:

`p(y | x) = Σ_z p_η(z | x) p_θ(y | x, z)`

Trong đó p_η(z | x) là mô hình truy xuất tài liệu liên quan và p_θ(y | x, z) là mô hình sinh câu trả lời dựa trên câu hỏi và tài liệu được truy xuất [6].

Hình 2.10 Mô hình RAG trong paper “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks”

> Chèn hình kiến trúc RAG-Sequence hoặc RAG-Token từ paper RAG [6].

### 2.6.2. Embedding, vector database và truy xuất ngữ nghĩa

Trong RAG, tài liệu y khoa được chia thành các đoạn nhỏ gọi là chunk. Mỗi chunk được biến đổi thành vector embedding và lưu trong vector database. Khi người dùng đặt câu hỏi, hệ thống tạo embedding cho câu hỏi rồi tìm các chunk gần nhất trong không gian vector. Độ tương đồng cosine giữa vector câu hỏi q và vector tài liệu d được tính:

`cos(q, d) = (q . d) / (||q|| ||d||)`

Đồ án sử dụng Chroma làm vector database và mô hình embedding đa ngôn ngữ để hỗ trợ câu hỏi tiếng Việt. Khi có kết quả phân tích ảnh, tên bệnh dự đoán được dùng như một gợi ý để truy xuất đúng phần tri thức liên quan. Đây là điểm quan trọng vì người dùng có thể hỏi bằng ngôn ngữ tự nhiên, trong khi tri thức nội bộ được tổ chức theo từng nhóm bệnh.

### 2.6.3. Sinh câu trả lời có ngữ cảnh

Sau khi truy xuất được ngữ cảnh y khoa, hệ thống đưa câu hỏi người dùng, tên bệnh dự đoán, tóm tắt phân tích ảnh và các đoạn tri thức liên quan vào mô hình ngôn ngữ. Mô hình sinh câu trả lời gồm triệu chứng tham khảo, nguyên nhân, hướng xử trí chung và lời khuyên đi khám khi cần. Phần prompt trong hệ thống yêu cầu trả lời bằng tiếng Việt, không bịa thông tin ngoài ngữ cảnh và luôn nhắc kết quả chỉ mang tính tham khảo.

Hình 2.11 Quy trình RAG trong hệ thống

> Chèn hình: Disease name + user prompt -> embedding -> Chroma DB -> retrieved medical context -> LLM generator -> generated response.
