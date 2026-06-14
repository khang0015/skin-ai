# 4.3. Kết quả phân loại bệnh

## 4.3.1. Kết quả huấn luyện mô hình phân loại

Trong đồ án, mô hình phân loại được xây dựng theo hướng kết hợp ba nhóm đặc trưng: VGG16 để khai thác đặc trưng cục bộ, khối Inception để bổ sung khả năng biểu diễn đa tỷ lệ, và Vision Transformer để học quan hệ giữa các vùng ảnh. Mô hình được đánh giá trên tập test gồm 1503 ảnh của bộ dữ liệu HAM10000 với 7 lớp bệnh: akiec, bcc, bkl, df, mel, nv và vasc.

Do dữ liệu HAM10000 có mất cân bằng lớp rõ rệt, accuracy không phản ánh đầy đủ chất lượng nhận diện trên các lớp ít mẫu. Vì vậy, trong quá trình thử nghiệm, macro-F1 được xem là chỉ số quan trọng bên cạnh accuracy. Kết quả ban đầu của mô hình VGG16 + Inception + Vision Transformer đạt test loss 0,7857, accuracy 0,876 và macro-F1 0,749. Sau khi nhận thấy macro-F1 vẫn còn hạn chế, đồ án điều chỉnh quá trình huấn luyện theo hướng ưu tiên hiệu quả trên các lớp thiểu số, bao gồm tăng cường dữ liệu, sử dụng trọng số lớp, focal loss, label smoothing, chiến lược fine-tuning theo giai đoạn và lưu checkpoint dựa trên validation macro-F1. Phiên bản VGG16+Inception+ViT_v4.ipynb được chọn làm mô hình chính vì cải thiện macro-F1 trên tập test lên 0,764, đồng thời vẫn giữ accuracy ở mức 0,870.

**Bảng 4.3. Kết quả cải thiện của mô hình phân loại**

| Phiên bản | Test loss | Test accuracy | Test macro-F1 | Số ảnh test |
|---|---:|---:|---:|---:|
| VGG16 + Inception + Vision Transformer | 0,7857 | 0,876 | 0,749 | 1503 |
| VGG16 + Inception + Vision Transformer v4 | 0,2256 | 0,870 | 0,764 | 1503 |

Kết quả cho thấy phiên bản v4 có accuracy giảm nhẹ từ 0,876 xuống 0,870, nhưng macro-F1 tăng từ 0,749 lên 0,764 và test loss giảm mạnh từ 0,7857 xuống 0,2256. Điều này phù hợp với mục tiêu của bài toán, vì trong bối cảnh dữ liệu mất cân bằng, mô hình không chỉ cần dự đoán tốt lớp chiếm đa số mà còn cần cải thiện khả năng nhận diện các lớp ít mẫu và các lớp có ý nghĩa lâm sàng cao.

Việc test loss giảm mạnh từ 0,7857 xuống 0,2256 có ý nghĩa quan trọng. Accuracy chỉ phản ánh tỷ lệ dự đoán đúng, trong khi loss phản ánh mức độ tự tin và chất lượng phân bố xác suất mà mô hình gán cho các lớp. Do đó, hai mô hình có accuracy gần tương đương vẫn có thể có loss rất khác nhau: nếu mô hình dự đoán đúng nhưng xác suất chưa chắc chắn, hoặc dự đoán sai với độ tự tin cao, loss sẽ lớn hơn. Ở phiên bản v4, loss giảm cho thấy mô hình không chỉ dự đoán đúng ở nhiều trường hợp mà còn đưa ra xác suất ổn định và hợp lý hơn cho lớp dự đoán. Điều này có thể đến từ việc sử dụng focal loss kết hợp trọng số lớp, label smoothing và cơ chế chọn checkpoint theo validation macro-F1, giúp mô hình học tốt hơn trên dữ liệu mất cân bằng và hạn chế các dự đoán quá lệch về lớp chiếm đa số. Tuy nhiên, loss thấp không có nghĩa mô hình đã giải quyết hoàn toàn bài toán, vì recall của một số lớp quan trọng như mel vẫn cần tiếp tục cải thiện.

**Hình 4.3. Đường cong loss, accuracy và macro-F1 trong quá trình huấn luyện classifier**

Chèn hình `report_assets/classifier/training_curves_VGG16_Inception_ViT_v4.png`.

**Hình 4.4. So sánh kết quả test trước và sau cải thiện theo macro-F1**

Chèn hình `report_assets/classifier/test_metric_change.png`.

## 4.3.2. Precision, recall và F1-score theo từng lớp

**Bảng 4.4. Classification report của mô hình phân loại chính**

| Lớp | Precision | Recall | F1-score | Support |
|---|---:|---:|---:|---:|
| akiec | 0,71 | 0,76 | 0,73 | 49 |
| bcc | 0,76 | 0,82 | 0,79 | 77 |
| bkl | 0,70 | 0,78 | 0,74 | 165 |
| df | 0,77 | 0,59 | 0,67 | 17 |
| mel | 0,76 | 0,63 | 0,69 | 167 |
| nv | 0,93 | 0,94 | 0,94 | 1006 |
| vasc | 0,89 | 0,73 | 0,80 | 22 |
| Macro avg | 0,79 | 0,75 | 0,76 | 1503 |
| Weighted avg | 0,87 | 0,87 | 0,87 | 1503 |

Mô hình dự đoán tốt nhất trên lớp nv với F1-score 0,94. Đây là lớp có số lượng mẫu lớn nhất trong tập test, nên mô hình có nhiều dữ liệu hơn để học đặc trưng ổn định. Các lớp bcc, bkl, akiec và vasc đạt F1-score lần lượt là 0,79, 0,74, 0,73 và 0,80, cho thấy mô hình đã cải thiện khả năng nhận diện nhiều lớp ngoài lớp đa số.

Lớp df có support rất nhỏ, chỉ 17 ảnh, nên kết quả cần được diễn giải thận trọng dù precision đạt 0,77 và F1-score đạt 0,67. Đối với lớp mel, precision đạt 0,76 nhưng recall đạt 0,63, cho thấy vẫn còn một số trường hợp melanoma bị dự đoán sang lớp khác. Đây là hạn chế cần nhấn mạnh vì melanoma là lớp có ý nghĩa lâm sàng cao; trong các hướng phát triển tiếp theo, cần tiếp tục ưu tiên cải thiện recall của lớp này.

**Hình 4.5. Precision, recall và F1-score theo từng lớp**

Chèn hình `report_assets/classifier/classification_report_v4_bar.png`.

## 4.3.3. Ma trận nhầm lẫn

**Bảng 4.5. Ma trận nhầm lẫn của mô hình phân loại chính**

| True \ Pred | akiec | bcc | bkl | df | mel | nv | vasc |
|---|---:|---:|---:|---:|---:|---:|---:|
| akiec | 37 | 4 | 3 | 1 | 1 | 3 | 0 |
| bcc | 2 | 63 | 6 | 0 | 3 | 3 | 0 |
| bkl | 7 | 3 | 128 | 0 | 10 | 17 | 0 |
| df | 0 | 2 | 1 | 10 | 0 | 4 | 0 |
| mel | 6 | 1 | 15 | 0 | 105 | 39 | 1 |
| nv | 0 | 8 | 28 | 1 | 20 | 948 | 1 |
| vasc | 0 | 2 | 1 | 1 | 0 | 2 | 16 |

**Hình 4.6. Ma trận nhầm lẫn trực quan**

Chèn hình `report_assets/classifier/confusion_matrix_v4.png`.

## 4.3.4. Phân tích các lớp dễ nhầm lẫn

Từ ma trận nhầm lẫn có thể thấy lỗi đáng chú ý nhất nằm ở lớp mel: 39 ảnh melanoma bị dự đoán thành nv và 15 ảnh bị dự đoán thành bkl. Đây là hiện tượng hợp lý về mặt hình ảnh vì các tổn thương sắc tố có thể có màu sắc, biên dạng hoặc cấu trúc tương đối giống nhau. Tuy nhiên, vì melanoma là lớp có rủi ro lâm sàng cao, việc nhầm melanoma sang các lớp lành tính hơn vẫn là hạn chế quan trọng của mô hình.

Lớp bkl cũng bị nhầm sang nv 17 ảnh và sang mel 10 ảnh, cho thấy ranh giới giữa các nhóm tổn thương sắc tố còn chưa hoàn toàn tách biệt. Lớp df có 4 ảnh bị nhầm sang nv, một phần do số lượng mẫu test của lớp này chỉ có 17 ảnh. Đối với lớp vasc, mô hình dự đoán đúng 16 trên 22 ảnh; mặc dù F1-score đạt 0,80, support nhỏ khiến kết quả của lớp này có độ dao động cao hơn các lớp nhiều mẫu.

Nhìn chung, phiên bản v4 cho thấy hướng tối ưu theo macro-F1 là phù hợp với bài toán phân loại tổn thương da trên dữ liệu mất cân bằng. Mô hình vẫn duy trì accuracy cao, đồng thời cải thiện khả năng cân bằng giữa các lớp. Các hướng cải thiện tiếp theo có thể tập trung vào tăng dữ liệu cho các lớp ít mẫu, áp dụng tăng cường dữ liệu có kiểm soát cho melanoma và dermatofibroma, hoặc thử nghiệm thêm các hàm mất mát/chiến lược lấy mẫu nhằm tăng recall cho các lớp có ý nghĩa lâm sàng cao.
