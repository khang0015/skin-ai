BÁO CÁO SƠ BỘ ĐỒ ÁN TỐT NGHIỆP
Tên đề tài: Xây dựng ứng dụng hỗ trợ chẩn đoán bệnh da liễu
Sinh viên thực hiện: [Điền họ tên]
Giảng viên hướng dẫn: [Điền họ tên]
Khoa/Ngành: [Điền thông tin]
Thời gian thực hiện: [Điền thời gian]
Ghi chú trình bày khi chuyển sang Microsoft Word: toàn bộ nội dung chính dùng Times New Roman, cỡ chữ 13, giãn dòng 1,3, căn đều hai lề. Tiêu đề chương dùng cỡ chữ 14, in đậm, căn giữa. Lề trang A4: trái 3 cm, phải 2 cm, trên 2,5 cm, dưới 2,5 cm. Đánh số trang bắt đầu từ phần MỞ ĐẦU.
 
MỞ ĐẦU
Bệnh da liễu là nhóm bệnh phổ biến, có biểu hiện lâm sàng đa dạng và nhiều trường hợp cần quan sát hình ảnh tổn thương để đưa ra nhận định ban đầu. Một số tổn thương lành tính có thể có hình thái tương tự tổn thương ác tính, trong khi một số bệnh nguy hiểm như melanoma cần được phát hiện sớm để tăng cơ hội điều trị hiệu quả. Trong thực tế, việc tiếp cận bác sĩ chuyên khoa da liễu không phải lúc nào cũng thuận lợi, đặc biệt ở các khu vực thiếu nhân lực y tế chuyên sâu. Vì vậy, các hệ thống hỗ trợ phân tích ảnh tổn thương da có thể đóng vai trò như một công cụ tham khảo ban đầu, giúp người dùng nhận biết mức độ nghi ngờ và được khuyến nghị thăm khám phù hợp.
Sự phát triển của thị giác máy tính, học sâu và mô hình ngôn ngữ lớn mở ra hướng tiếp cận mới cho bài toán hỗ trợ chẩn đoán. Thay vì chỉ phân loại toàn bộ ảnh thành một nhãn bệnh, hệ thống trong đồ án được thiết kế theo pipeline nhiều bước: kiểm tra ảnh có phải ảnh da hay không, phát hiện vùng tổn thương bằng mô hình YOLO, phân loại tổn thương bằng mô hình VGG16 kết hợp Vision Transformer, sau đó sử dụng pipeline truy xuất tăng cường sinh văn bản để tạo phản hồi tư vấn bằng tiếng Việt. Cách tổ chức này giúp hệ thống không chỉ đưa ra nhãn dự đoán mà còn giải thích thêm dựa trên cơ sở tri thức cục bộ.
Đề tài tập trung xây dựng một ứng dụng web có khả năng nhận ảnh từ người dùng, phân tích ảnh, hiển thị vùng tổn thương, trả về nhãn bệnh dự đoán và cho phép người dùng trao đổi thêm bằng hội thoại. Hệ thống có backend sử dụng FastAPI, frontend dùng HTML, CSS, JavaScript thuần, cơ sở dữ liệu PostgreSQL để lưu lịch sử hội thoại và cấu hình pipeline, đồng thời sử dụng Chroma làm kho vector cho phần truy xuất tri thức.
Mục tiêu của đồ án không phải thay thế bác sĩ, mà xây dựng một hệ thống hỗ trợ tham khảo có biên cảnh báo rõ ràng. Mọi kết quả dự đoán cần được xác nhận bởi bác sĩ da liễu hoặc xét nghiệm chuyên môn khi cần thiết.
 
CHƯƠNG 1: GIỚI THIỆU TỔNG QUAN ĐỀ TÀI
1.1. Bối cảnh và lý do chọn đề tài
Da là cơ quan bao phủ bên ngoài cơ thể và cũng là nơi dễ quan sát các thay đổi bất thường như nốt sắc tố, mảng đỏ, vùng loét, sẩn, vảy, khối u nhỏ hoặc vùng đổi màu. Trong khám da liễu, hình ảnh tổn thương có vai trò quan trọng vì nhiều bệnh có biểu hiện trực quan rõ rệt. Tuy nhiên, việc đánh giá tổn thương da không đơn giản, đặc biệt đối với các tổn thương sắc tố. Một nốt ruồi lành tính có thể có màu sẫm và đường viền không đều, trong khi một tổn thương ác tính ở giai đoạn đầu đôi khi chưa biểu hiện rõ. Vì vậy, chẩn đoán da liễu thường cần kết hợp tiền sử bệnh, quan sát lâm sàng, soi da, theo dõi tiến triển và trong một số trường hợp cần sinh thiết để xác nhận bằng mô bệnh học.
Theo Tổ chức Y tế Thế giới, ung thư da chủ yếu liên quan đến phơi nhiễm tia cực tím từ ánh nắng mặt trời hoặc nguồn nhân tạo như giường tắm nắng. Nguồn này cũng ghi nhận năm 2020 có hơn 1,5 triệu ca ung thư da và hơn 120.000 ca tử vong liên quan ung thư da trên toàn cầu [7]. Các số liệu trên cho thấy bệnh da liễu, đặc biệt là nhóm bệnh có nguy cơ ung thư, không chỉ là vấn đề thẩm mỹ mà còn là vấn đề sức khỏe cộng đồng. Trong đó, melanoma là loại ung thư da nguy hiểm vì có khả năng di căn và gây tử vong nếu phát hiện muộn. Hiệp hội Ung thư Hoa Kỳ cho biết tỷ lệ sống tương đối 5 năm của melanoma giai đoạn khu trú là trên 99%, nhưng giảm còn 35% khi bệnh đã di căn xa, dựa trên dữ liệu người bệnh được chẩn đoán trong giai đoạn 2015-2021 [8]. Điều này nhấn mạnh ý nghĩa của phát hiện sớm và định hướng thăm khám kịp thời.
Sự phát triển của học sâu trong thị giác máy tính tạo ra cơ hội xây dựng các hệ thống hỗ trợ phân tích ảnh da liễu. Nghiên cứu của Esteva và cộng sự trên tạp chí Nature đã chứng minh tiềm năng của mạng nơ-ron tích chập trong phân loại ung thư da từ ảnh, với nhận định rằng thiết bị di động kết hợp mạng nơ-ron sâu có thể mở rộng khả năng tiếp cận chuyên môn da liễu ra ngoài phòng khám [9]. Đây là hướng nghiên cứu có giá trị thực tiễn vì ảnh tổn thương da có thể được thu thập tương đối dễ dàng bằng điện thoại hoặc thiết bị chụp ảnh thông thường, dù chất lượng ảnh vẫn cần được kiểm soát.
Bên cạnh đó, các bộ dữ liệu chuẩn đã thúc đẩy nghiên cứu tự động hóa chẩn đoán ảnh da liễu. Bộ dữ liệu HAM10000 được công bố nhằm giải quyết hạn chế về quy mô và độ đa dạng của dữ liệu ảnh soi da trước đây. Trong bài báo gốc, nhóm tác giả viết rằng "final dataset consists of 10015 dermatoscopic images" [1]. Bộ dữ liệu này bao gồm nhiều nhóm tổn thương sắc tố thường gặp, được sử dụng rộng rãi để huấn luyện và đánh giá mô hình phân loại ảnh da liễu. Việc sử dụng các bộ dữ liệu như vậy giúp sinh viên và nhà nghiên cứu có cơ sở thực nghiệm rõ ràng khi phát triển mô hình học sâu.
Từ các bối cảnh trên, đề tài "Xây dựng ứng dụng hỗ trợ chẩn đoán bệnh da liễu" được lựa chọn nhằm kết hợp mô hình thị giác máy tính và mô hình sinh ngôn ngữ trong một ứng dụng hoàn chỉnh. Hệ thống không chỉ dừng ở việc đưa ra một nhãn dự đoán, mà còn kiểm tra ảnh đầu vào, phát hiện vùng tổn thương, phân loại bệnh, truy xuất tri thức y khoa liên quan và tạo phản hồi bằng tiếng Việt cho người dùng. Đây là hướng tiếp cận phù hợp với nhu cầu thực tế, vì người dùng phổ thông thường cần một giải thích dễ hiểu sau kết quả phân tích, đồng thời cần được nhắc rõ rằng hệ thống chỉ mang tính hỗ trợ, không thay thế bác sĩ.
1.2. Mục tiêu nghiên cứu
Mục tiêu tổng quát của đề tài là xây dựng một ứng dụng web hỗ trợ phân tích ảnh tổn thương da và cung cấp phản hồi tham khảo bằng tiếng Việt dựa trên kết quả phân tích ảnh kết hợp cơ sở tri thức da liễu. Ứng dụng được định hướng như một công cụ hỗ trợ ban đầu, giúp người dùng nhận biết tổn thương có thể thuộc nhóm bệnh nào, hiểu thêm thông tin cơ bản về nhóm bệnh đó và có cơ sở cân nhắc việc thăm khám chuyên khoa.
Về mặt xử lý ảnh, đề tài hướng đến xây dựng một pipeline gồm nhiều bước rõ ràng. Ảnh đầu vào trước hết được kiểm tra có chứa vùng da hay không, nhằm hạn chế trường hợp người dùng tải ảnh không phù hợp nhưng hệ thống vẫn đưa ra dự đoán. Sau đó, mô hình phát hiện đối tượng được sử dụng để xác định vùng nghi ngờ tổn thương trên ảnh. Trong phạm vi đồ án, hai phiên bản mô hình YOLOv8 và YOLOv11 được tích hợp để phục vụ phát hiện vùng tổn thương. Kết quả phát hiện được chuyển sang bộ phân loại, trong đó mô hình chính được xây dựng theo hướng kết hợp VGG16 với Vision Transformer nhằm tận dụng cả khả năng học đặc trưng cục bộ của mạng tích chập và khả năng mô hình hóa quan hệ không gian của cơ chế chú ý.
Về mặt sinh phản hồi, đề tài hướng đến xây dựng một pipeline truy xuất tăng cường sinh văn bản. Sau khi có kết quả phân tích ảnh, hệ thống truy xuất các đoạn tri thức liên quan trong cơ sở tri thức nội bộ, đưa ngữ cảnh này cùng tóm tắt phân tích ảnh vào mô hình ngôn ngữ để tạo câu trả lời. Cách làm này giúp câu trả lời không chỉ dựa vào nhãn dự đoán mà còn gắn với thông tin mô tả bệnh, dấu hiệu tham khảo, khuyến nghị thăm khám và cảnh báo an toàn.
Về mặt ứng dụng, đề tài cần xây dựng giao diện người dùng cho phép gửi ảnh, gửi câu hỏi, xem kết quả phân tích, xem vùng tổn thương được đánh dấu và tiếp tục trao đổi trong cùng một hội thoại. Ngoài ra, hệ thống cần có giao diện quản trị để lựa chọn pipeline, thay đổi detector, classifier và cấu hình đầu vào cho bộ phân loại. Mục tiêu này giúp ứng dụng không chỉ là một mô hình thử nghiệm trong notebook, mà là một hệ thống có thể vận hành, kiểm thử và mở rộng.
1.3. Đối tượng sử dụng
Đối tượng sử dụng đầu tiên của hệ thống là người dùng phổ thông có nhu cầu tham khảo thông tin ban đầu về một tổn thương da. Người dùng có thể tải ảnh vùng da cần kiểm tra, đặt câu hỏi về triệu chứng hoặc hỏi thêm về kết quả phân tích. Với nhóm người dùng này, hệ thống cần trình bày kết quả bằng tiếng Việt dễ hiểu, tránh thuật ngữ khó khi không cần thiết và luôn kèm cảnh báo rằng kết quả không phải chẩn đoán y khoa cuối cùng.
Đối tượng sử dụng thứ hai là sinh viên, giảng viên hoặc nhà nghiên cứu trong lĩnh vực công nghệ thông tin, trí tuệ nhân tạo và tin học y sinh. Với nhóm này, hệ thống có giá trị như một mô hình minh họa đầy đủ cho việc đưa học sâu vào ứng dụng thực tế. Người nghiên cứu có thể thay đổi mô hình phát hiện, mô hình phân loại, nguồn tài liệu tri thức hoặc mô hình sinh văn bản để so sánh hiệu quả giữa các phương án.
Đối tượng sử dụng thứ ba là người quản trị hệ thống hoặc người vận hành thử nghiệm. Người quản trị cần theo dõi pipeline đang được sử dụng, lựa chọn mô hình mặc định, cập nhật cấu hình và kiểm tra trạng thái của hệ thống. Vì vậy, đồ án xây dựng thêm trang quản trị để thay đổi cấu hình detector, classifier và pipeline mà không cần can thiệp trực tiếp vào mã nguồn.
Trong mọi trường hợp, hệ thống không được định nghĩa là công cụ dành cho bác sĩ để đưa ra quyết định điều trị thay thế quy trình chuyên môn. Kết quả phân tích chỉ nên được xem là thông tin tham khảo, có thể hỗ trợ người dùng chuẩn bị câu hỏi trước khi đi khám hoặc hỗ trợ quá trình học tập, nghiên cứu và thử nghiệm kỹ thuật.
1.4. Ý nghĩa thực tiễn
Ý nghĩa thực tiễn đầu tiên của đề tài là hỗ trợ người dùng tiếp cận thông tin da liễu ban đầu một cách thuận tiện hơn. Thay vì chỉ tìm kiếm rời rạc trên mạng, người dùng có thể gửi ảnh, nhận kết quả phân tích và đọc phần giải thích liên quan đến nhóm tổn thương được dự đoán. Hệ thống cũng có thể nhắc người dùng chú ý các dấu hiệu nguy cơ như tổn thương thay đổi nhanh, chảy máu, loét, không đối xứng, bờ không đều hoặc màu sắc không đồng nhất. Những thông tin này không thay thế bác sĩ nhưng có thể giúp người dùng chủ động hơn trong việc theo dõi sức khỏe.
Ý nghĩa thứ hai là hỗ trợ phát hiện sớm các trường hợp cần thăm khám. Như đã trình bày, tiên lượng của melanoma khác biệt rất lớn giữa giai đoạn khu trú và giai đoạn di căn xa [8]. Một ứng dụng hỗ trợ không thể khẳng định người dùng mắc bệnh hay không, nhưng có thể góp phần định hướng rằng các tổn thương nghi ngờ nên được bác sĩ da liễu kiểm tra. Đặc biệt, trong bối cảnh người dùng có thể trì hoãn khám vì chủ quan hoặc thiếu thông tin, một phản hồi tham khảo có cảnh báo rõ ràng có thể mang lại giá trị thực tế.
Ý nghĩa thứ ba là tạo nền tảng triển khai nghiên cứu trí tuệ nhân tạo trong y tế theo hướng có trách nhiệm. Đồ án không chỉ xây dựng một mô hình phân loại đơn lẻ, mà tổ chức thành một hệ thống có kiểm tra đầu vào, lưu lịch sử, hiển thị vùng tổn thương, truy xuất tri thức và sinh phản hồi có giới hạn. Cách tiếp cận này phù hợp với yêu cầu của ứng dụng y tế, nơi độ chính xác của mô hình cần đi kèm khả năng giải thích, kiểm soát nguồn thông tin và cảnh báo rủi ro.
Đối với đào tạo và nghiên cứu, đề tài cung cấp một ví dụ cụ thể về quy trình chuyển từ mô hình học sâu sang ứng dụng. Sinh viên không chỉ huấn luyện mô hình trên dữ liệu ảnh mà còn phải xử lý bài toán giao diện, lập trình giao diện lập trình ứng dụng, cơ sở dữ liệu, cấu hình mô hình, truy xuất văn bản, lưu trữ lịch sử và triển khai thử nghiệm. Đây là những kỹ năng cần thiết khi phát triển sản phẩm trí tuệ nhân tạo trong thực tế.
1.5. Phạm vi và giới hạn nghiên cứu
Phạm vi bệnh của đề tài tập trung vào các nhóm tổn thương da tương ứng với bộ dữ liệu HAM10000, gồm actinic keratosis hoặc Bowen's disease, basal cell carcinoma, benign keratosis, dermatofibroma, melanoma, melanocytic nevus và vascular lesion. Đây là các nhóm tổn thương sắc tố và tổn thương liên quan thường được dùng trong nghiên cứu phân loại ảnh soi da. Đề tài không đặt mục tiêu bao phủ toàn bộ bệnh da liễu như viêm da cơ địa, viêm da tiếp xúc, vảy nến, mề đay, nấm da, mụn trứng cá hoặc các bệnh nhiễm trùng da nếu những bệnh này không nằm trong dữ liệu huấn luyện và cơ sở tri thức.
Phạm vi dữ liệu của đề tài chủ yếu dựa trên ảnh tổn thương da và thông tin tri thức được chuẩn bị trong cơ sở dữ liệu nội bộ. Ảnh đầu vào được xem xét ở góc độ phân tích hình ảnh, chưa kết hợp đầy đủ các yếu tố lâm sàng như tuổi, giới tính, vị trí tổn thương, thời gian xuất hiện, tiền sử bệnh, tiền sử gia đình, mức độ phơi nắng hoặc kết quả xét nghiệm. Đây là giới hạn quan trọng vì trong thực hành y khoa, chẩn đoán không chỉ dựa trên ảnh.
Phạm vi kỹ thuật của đề tài là xây dựng hệ thống nguyên mẫu có thể chạy cục bộ hoặc trên môi trường thử nghiệm. Backend sử dụng FastAPI, frontend sử dụng HTML, CSS và JavaScript, cơ sở dữ liệu PostgreSQL lưu lịch sử hội thoại và cấu hình, Chroma lưu vector tri thức cho phần truy xuất. Mô hình phát hiện vùng tổn thương gồm YOLOv8 và YOLOv11. Mô hình phân loại chính là VGG16 kết hợp Vision Transformer. Phần sinh câu trả lời có thể sử dụng OpenAI hoặc Ollama tùy cấu hình.
Giới hạn lớn nhất của hệ thống là không thể thay thế bác sĩ da liễu. Nghiên cứu của Esteva và cộng sự cho thấy học sâu có tiềm năng cao trong phân loại ảnh da liễu, nhưng chính bài toán này vẫn phụ thuộc nhiều vào chất lượng dữ liệu, phân bố bệnh, điều kiện chụp ảnh và xác nhận chuyên môn [9]. Trong ứng dụng thực tế, ảnh người dùng có thể bị mờ, thiếu sáng, lệch màu, chụp quá xa, che khuất vùng tổn thương hoặc không giống ảnh soi da trong bộ dữ liệu huấn luyện. Do đó, hệ thống cần được trình bày là công cụ hỗ trợ tham khảo, không phải công cụ chẩn đoán độc lập.
1.6. Phương pháp nghiên cứu và triển khai
Phương pháp nghiên cứu của đề tài bắt đầu từ việc khảo sát bài toán phân tích ảnh da liễu và các hướng tiếp cận học sâu đã được công bố. Các tài liệu nền tảng bao gồm nghiên cứu về bộ dữ liệu HAM10000, mô hình phát hiện đối tượng YOLO, mạng tích chập VGG, Vision Transformer và truy xuất tăng cường sinh văn bản. Các tài liệu y tế từ Tổ chức Y tế Thế giới và Hiệp hội Ung thư Hoa Kỳ được sử dụng để trình bày bối cảnh sức khỏe cộng đồng, nguy cơ tia cực tím và ý nghĩa phát hiện sớm ung thư da.
Sau bước khảo sát, đề tài triển khai mô hình theo hướng module hóa. Bộ phát hiện ảnh da được xây dựng bằng phương pháp xử lý ảnh truyền thống dựa trên không gian màu HSV và YCrCb. Mục tiêu của bước này là kiểm tra sơ bộ ảnh đầu vào trước khi chạy mô hình học sâu. Tiếp theo, mô hình YOLO được dùng để phát hiện vùng tổn thương. Việc dùng detector giúp hệ thống xác định vùng quan tâm, hiển thị bounding box cho người dùng và cung cấp vùng ảnh phù hợp cho bước phân loại.
Đối với phân loại ảnh, đề tài xây dựng mô hình kết hợp VGG16 và Vision Transformer. VGG16 đóng vai trò trích xuất đặc trưng cục bộ từ ảnh, trong khi phần Transformer học quan hệ giữa các vùng đặc trưng sau khi đã được mã hóa thành chuỗi patch. Hướng kết hợp này được lựa chọn vì ảnh tổn thương da vừa có đặc trưng cục bộ như màu sắc, đường viền, cấu trúc nhỏ, vừa có đặc trưng toàn cục như hình dạng tổng thể và sự phân bố không đều của vùng tổn thương.
Đối với phần trả lời người dùng, đề tài triển khai pipeline truy xuất tăng cường sinh văn bản. Tài liệu tri thức được nạp, chia thành các đoạn nhỏ, biến đổi thành vector bằng mô hình embedding đa ngôn ngữ và lưu vào Chroma. Khi người dùng đặt câu hỏi, hệ thống truy xuất các đoạn liên quan, kết hợp với kết quả phân tích ảnh và lịch sử hội thoại để tạo câu trả lời tiếng Việt. Phương pháp này giúp giảm tình trạng câu trả lời quá chung chung, đồng thời tạo cơ sở để kiểm soát nguồn thông tin.
Cuối cùng, hệ thống được triển khai thành ứng dụng web. Backend cung cấp các giao diện lập trình ứng dụng cho phân tích ảnh, hỏi đáp, hội thoại, lịch sử và quản trị. Frontend cung cấp giao diện tải ảnh, nhập câu hỏi, hiển thị kết quả phân tích, xem ảnh có vùng phát hiện và mở lại hội thoại cũ. Cơ sở dữ liệu lưu client ẩn danh, cuộc hội thoại, tin nhắn, kết quả phân tích ảnh và cấu hình model registry. Cách triển khai này giúp đồ án có thể được kiểm thử theo luồng sử dụng thực tế thay vì chỉ đánh giá mô hình rời rạc.
1.7. Điểm mới và sự khác biệt của đề tài
Điểm khác biệt đầu tiên của đề tài là xây dựng hệ thống theo pipeline hoàn chỉnh từ ảnh đầu vào đến phản hồi hội thoại. Nhiều bài toán phân loại ảnh da liễu chỉ tập trung vào việc đưa ảnh vào mô hình và trả về nhãn. Trong khi đó, đồ án bổ sung bước kiểm tra ảnh da, phát hiện vùng tổn thương, phân loại, truy xuất tri thức, sinh câu trả lời và lưu lịch sử hội thoại. Cách tổ chức này gần với một ứng dụng thực tế hơn so với một mô hình thử nghiệm đơn lẻ.
Điểm khác biệt thứ hai là mô hình phân loại được thiết kế theo hướng kết hợp mạng tích chập và Transformer. VGG16 giúp học các đặc trưng hình ảnh cục bộ, module Inception làm giàu đặc trưng đa nhánh, còn Vision Transformer giúp mô hình hóa mối quan hệ giữa các vùng ảnh. Sự kết hợp này phù hợp với ảnh tổn thương da, nơi thông tin chẩn đoán có thể nằm ở cả chi tiết nhỏ của bề mặt tổn thương và cấu trúc tổng thể của vùng sắc tố.
Điểm khác biệt thứ ba là hệ thống có cơ chế truy xuất tri thức trước khi sinh câu trả lời. Thay vì để mô hình ngôn ngữ trả lời hoàn toàn theo tri thức nội tại, hệ thống truy xuất các đoạn liên quan từ cơ sở tri thức nội bộ rồi đưa vào prompt. Điều này đặc biệt quan trọng trong miền y tế, vì câu trả lời cần được giới hạn trong phạm vi thông tin có kiểm soát, tránh đưa ra khẳng định quá mức hoặc khuyến nghị điều trị không có căn cứ.
Điểm khác biệt thứ tư là hệ thống được xây dựng với khả năng mở rộng mô hình. Detector, classifier và pipeline được khai báo trong model registry. Người quản trị có thể thay đổi mô hình mặc định thông qua giao diện quản trị, còn nhà phát triển có thể bổ sung adapter mới khi muốn thử nghiệm mô hình khác. Nhờ đó, đề tài có thể tiếp tục phát triển sau giai đoạn bảo vệ, chẳng hạn thêm mô hình phân loại mới, thay đổi embedding, mở rộng cơ sở tri thức hoặc triển khai thêm chức năng xuất báo cáo.
Tóm lại, Chương 1 đã trình bày bối cảnh, mục tiêu, đối tượng sử dụng, ý nghĩa thực tiễn, phạm vi, phương pháp triển khai và điểm mới của đề tài. Những nội dung này là nền tảng để các chương sau trình bày chi tiết hơn về cơ sở lý thuyết, phân tích thiết kế hệ thống, cài đặt, thử nghiệm và đánh giá kết quả.
 
CHƯƠNG 2: CƠ SỞ LÝ THUYẾT
2.1. Bài toán hỗ trợ chẩn đoán bệnh da liễu từ ảnh
2.1.1. Đặc điểm ảnh tổn thương da
Ảnh tổn thương da là nguồn dữ liệu trực quan quan trọng trong khám da liễu. Một ảnh có thể chứa nhiều dấu hiệu liên quan đến chẩn đoán như màu sắc, bờ tổn thương, hình dạng tổng thể, cấu trúc sắc tố, vùng loét, mạch máu và mức độ không đồng nhất của bề mặt. Một số dấu hiệu nằm ở vùng rất nhỏ, chẳng hạn chấm sắc tố hoặc đường viền bất thường, trong khi một số dấu hiệu khác cần quan sát toàn bộ vùng tổn thương, chẳng hạn sự bất đối xứng hoặc phân bố màu không đều. Vì vậy, bài toán phân tích ảnh da liễu cần mô hình có khả năng học cả đặc trưng cục bộ và đặc trưng toàn cục.
Với người đọc chưa quen với trí tuệ nhân tạo, có thể hiểu đơn giản rằng hệ thống không “nhìn” ảnh giống con người, mà biến ảnh thành các ma trận số rồi học quy luật từ nhiều ví dụ đã được gán nhãn. Khi dữ liệu có nhiều trường hợp giống nhau về màu sắc hoặc hình dạng, mô hình cũng có thể nhầm giữa các lớp bệnh có biểu hiện gần nhau. Vì vậy, báo cáo cần trình bày rõ dữ liệu đến từ đâu, ảnh được xử lý như thế nào, mô hình học đặc trưng gì và kết quả sai thường rơi vào nhóm nào.
Trong phạm vi đồ án, hệ thống không đưa ra chẩn đoán y khoa cuối cùng. Mục tiêu là hỗ trợ phân tích ảnh, phát hiện vùng tổn thương, phân loại nhóm bệnh tham khảo và sinh phản hồi giải thích bằng tiếng Việt. Điều này phù hợp với bản chất của ứng dụng hỗ trợ: mô hình học máy cung cấp thông tin ban đầu, còn quyết định y khoa vẫn cần bác sĩ da liễu xác nhận.
2.1.2. Pipeline tổng quát của đề tài
Pipeline của đồ án gồm các bước chính: ảnh đầu vào, kiểm tra ảnh da, phát hiện vùng tổn thương bằng YOLO, phân loại bằng mô hình lai VGG16, Inception và Vision Transformer, sau đó đưa tên bệnh cùng câu hỏi của người dùng vào pipeline truy xuất tăng cường sinh văn bản để tạo phản hồi. Việc tổ chức pipeline nhiều bước giúp hệ thống giảm rủi ro ở từng giai đoạn. Nếu ảnh không phải ảnh da, hệ thống dừng sớm. Nếu ảnh hợp lệ, YOLO xác định vùng tổn thương để mô hình phân loại tập trung vào vùng có ý nghĩa. Sau khi có kết quả phân loại, RAG bổ sung ngữ cảnh y khoa để câu trả lời không chỉ là một nhãn bệnh rời rạc.
Lý do không thiết kế hệ thống theo kiểu một mô hình duy nhất là vì người dùng phổ thông thường gửi ảnh trong điều kiện không chuẩn: ánh sáng khác nhau, vùng da không nằm giữa ảnh, ảnh có nền thừa hoặc tổn thương chiếm diện tích nhỏ. Bước kiểm tra ảnh da giúp loại ảnh không liên quan. Bước phát hiện vùng tổn thương giúp thu hẹp vùng quan sát. Bước phân loại đưa ra nhãn bệnh có độ tin cậy. Cuối cùng, bước truy xuất tri thức giúp giải thích kết quả bằng ngôn ngữ gần với người dùng hơn. Nhờ đó, pipeline trở thành một quy trình xử lý có thể giải thích được, thay vì chỉ là một “hộp đen” trả về tên bệnh.
Hình 2.1 Pipeline tổng thể của hệ thống hỗ trợ chẩn đoán bệnh da liễu
Chèn hình pipeline tổng thể: Input Image -> Skin Detection Module -> YOLO Detection -> Crop Diseased Region -> CNN Classifier -> RAG Pipeline -> Generated Response.
2.2. Dữ liệu sử dụng trong đề tài
2.2.1. Bộ dữ liệu HAM10000 cho phân loại bệnh
HAM10000 là bộ dữ liệu gồm 10015 ảnh soi da của các tổn thương sắc tố thường gặp. Theo paper gốc, bộ dữ liệu được thu thập từ nhiều nguồn, nhiều quần thể và nhiều thiết bị khác nhau, nhờ đó tăng độ đa dạng so với các bộ dữ liệu nhỏ trước đây [1]. Trong bài báo, nhóm tác giả mô tả bộ dữ liệu bằng đoạn trích: "final dataset consists of 10015 dermatoscopic images" [1]. Đồ án sử dụng HAM10000 cho bài toán phân loại bảy lớp bệnh, không dùng bộ này để huấn luyện YOLO.
Bảng 2.1 Các lớp bệnh trong phạm vi đồ án
Mã lớp	Tên tiếng Anh	Diễn giải tiếng Việt
akiec	Actinic keratosis / Bowen's disease	Dày sừng ánh sáng hoặc bệnh Bowen, có liên quan tổn thương tiền ung thư
bcc	Basal cell carcinoma	Ung thư biểu mô tế bào đáy
bkl	Benign keratosis	Nhóm dày sừng lành tính, gồm seborrheic keratosis và solar lentigo
df	Dermatofibroma	U xơ bì, thường lành tính
mel	Melanoma	Ung thư hắc tố, nhóm nguy hiểm cần phát hiện sớm
nv	Melanocytic nevus	Nốt ruồi sắc tố, thường lành tính
vasc	Vascular lesion	Tổn thương mạch máu như hemangioma hoặc angiokeratoma

HAM10000 có hiện tượng mất cân bằng dữ liệu. Lớp melanocytic nevus chiếm tỷ lệ lớn, trong khi dermatofibroma hoặc vascular lesion có số lượng ít hơn nhiều. Vì vậy, accuracy không đủ để đánh giá toàn diện mô hình. Khi báo cáo kết quả phân loại, cần bổ sung precision, recall, F1-score theo từng lớp và ma trận nhầm lẫn để xem mô hình có bỏ sót lớp hiếm hay không.
2.2.2. Bộ dữ liệu ISIC 2018 Task 1 cho huấn luyện YOLO
YOLO trong đồ án không được huấn luyện trên HAM10000. Theo notebook yolo_dataset_labeling.ipynb, dữ liệu YOLO được lấy từ ISIC 2018 Challenge Task 1: Lesion Boundary Segmentation. Bộ dữ liệu này cung cấp ảnh tổn thương da và mask ground truth tương ứng, phù hợp cho việc tạo bounding box huấn luyện detector. Trang ISIC Challenge mô tả rằng ground truth dùng cho huấn luyện được tạo bằng nhiều kỹ thuật và được rà soát bởi bác sĩ da liễu có chuyên môn soi da [15]. Paper tổng kết ISIC 2018 cũng cho biết challenge gồm hơn 12.500 ảnh qua ba tác vụ: segmentation, attribute detection và disease classification [16].
Trong notebook, ảnh gốc được lấy từ thư mục ISIC2018_Task1-2_Training_Input, mask lấy từ ISIC2018_Task1_Training_GroundTruth. Với mỗi ảnh, mask _segmentation.png được nhị phân hóa, tìm contour ngoài lớn nhất, sau đó dùng cv2.boundingRect để lấy bounding box bao quanh vùng tổn thương. Nhãn YOLO được lưu theo một lớp duy nhất là lesion.
Công thức chuyển từ bounding box pixel sang nhãn YOLO như sau. Gọi kích thước ảnh là W x H, bounding box có góc trái trên là (x, y), chiều rộng w và chiều cao h. Khi đó:
x_center = (x + w / 2) / W
y_center = (y + h / 2) / H
width = w / W
height = h / H
Mỗi file nhãn có dạng: 0 x_center y_center width height. Trong đó 0 là mã lớp lesion. Notebook chia dữ liệu thành train, validation và test theo tỷ lệ 70%, 15%, 15% bằng train_test_split, sau đó lưu theo cấu trúc chuẩn YOLO: images/train, images/val, images/test, labels/train, labels/val, labels/test.
Hình 2.2 Minh họa chuyển mask phân đoạn ISIC 2018 thành bounding box YOLO
Chèn hình gồm ba phần: ảnh gốc, mask ground truth, bounding box tạo từ contour lớn nhất.
2.2.3. Vấn đề mất cân bằng dữ liệu và chỉ số đánh giá
Với bài toán phân loại bệnh, mất cân bằng lớp có thể khiến mô hình thiên về lớp xuất hiện nhiều. Vì vậy, bên cạnh accuracy, báo cáo cần dùng macro precision, macro recall và macro F1-score. Precision phản ánh mức độ dự đoán đúng trong các mẫu được gán vào một lớp; recall phản ánh khả năng tìm đủ mẫu thật của lớp đó; F1-score cân bằng giữa precision và recall. Với bài toán phát hiện vùng tổn thương, cần dùng precision, recall và mean Average Precision dựa trên ngưỡng IoU.
Điểm cần nhấn mạnh là accuracy không đủ thuyết phục trong dữ liệu mất cân bằng. Nếu một lớp chiếm tỷ lệ rất lớn, mô hình có thể đạt accuracy cao bằng cách dự đoán tốt lớp lớn nhưng vẫn bỏ sót lớp hiếm. Trong bài toán da liễu, điều này đặc biệt nguy hiểm vì một số lớp ít mẫu lại có ý nghĩa lâm sàng cao. Vì vậy, đồ án sử dụng thêm macro-F1 để đánh giá công bằng hơn giữa các lớp. Macro-F1 tính trung bình F1-score của từng lớp mà không ưu tiên lớp có nhiều ảnh, nhờ đó phản ánh rõ hơn khả năng nhận diện các lớp nhỏ như dermatofibroma hoặc vascular lesions.
Về mặt huấn luyện, đồ án sử dụng các kỹ thuật giảm ảnh hưởng của mất cân bằng dữ liệu như lấy mẫu có trọng số và hàm mất mát có trọng số theo lớp. Class-Balanced Loss dựa trên khái niệm “số mẫu hiệu dụng”, với công thức E_n = (1 - β^n) / (1 - β), trong đó n là số mẫu của lớp và β là tham số điều chỉnh [18]. Khi kết hợp với Focal Loss, mô hình được khuyến khích chú ý nhiều hơn đến các mẫu khó và các lớp ít dữ liệu, thay vì chỉ tối ưu cho lớp chiếm đa số [17].
2.3. Cơ sở lý thuyết mạng tích chập
2.3.1. Phép tích chập, hàm kích hoạt và pooling
Mạng tích chập là nền tảng của nhiều mô hình thị giác máy tính. Với ảnh đầu vào X, bộ lọc W và bias b, phép tích chập tại vị trí (i, j) của kênh đầu ra k có thể viết:
Y(i, j, k) = b_k + Σ_c Σ_u Σ_v W(u, v, c, k) . X(i + u, j + v, c)
Công thức trên cho thấy mỗi bộ lọc học một mẫu đặc trưng cục bộ trên ảnh, chẳng hạn cạnh, màu, cấu trúc sắc tố hoặc vùng chuyển tiếp. Sau tích chập, mô hình thường dùng hàm kích hoạt phi tuyến. Hàm ReLU được dùng phổ biến:
ReLU(x) = max(0, x)
Pooling giúp giảm kích thước không gian của feature map, giảm chi phí tính toán và tăng tính ổn định trước những thay đổi nhỏ trong ảnh. Ở tầng cuối, mô hình phân loại thường dùng softmax để chuyển logits z thành xác suất:
p_i = exp(z_i) / Σ_j exp(z_j)
Hàm mất mát phân loại phổ biến là cross-entropy:
L = - Σ_i y_i log(p_i)
Trong đó y_i là nhãn thật ở dạng one-hot và p_i là xác suất dự đoán của lớp i.
Nếu diễn giải trực quan, các tầng đầu của mạng tích chập thường học những mẫu đơn giản như cạnh, màu và vùng chuyển sắc. Các tầng sâu hơn kết hợp các mẫu nhỏ này thành đặc trưng có ý nghĩa hơn như bờ tổn thương, vùng sắc tố không đều hoặc cấu trúc tổng thể. Đây là lý do mạng tích chập phù hợp với ảnh da liễu: nó không cần người lập trình viết sẵn quy tắc nhận dạng từng dấu hiệu, mà tự học các đặc trưng từ dữ liệu gán nhãn.
Hình 2.3 Phép tích chập trong mạng CNN
Chèn hình minh họa phép tích chập: ảnh đầu vào, kernel trượt và feature map đầu ra.
2.3.2. VGG16
VGG16 là một kiến trúc mạng tích chập kinh điển, nổi bật nhờ việc sử dụng nhiều bộ lọc nhỏ 3 x 3 và tăng chiều sâu mạng một cách có hệ thống. Simonyan và Zisserman cho thấy việc tăng độ sâu lên "16-19 weight layers" giúp cải thiện hiệu quả phân loại ảnh [4]. Thiết kế của VGG đơn giản: nhiều lớp tích chập 3 x 3 được xếp liên tiếp, sau đó là pooling và các lớp fully connected. Nhờ cấu trúc rõ ràng, VGG16 thường được dùng làm backbone hoặc bộ trích xuất đặc trưng trong nhiều bài toán ảnh y tế.
Trong paper VGG, đóng góp chính được mô tả là đánh giá mạng ngày càng sâu với các bộ lọc tích chập rất nhỏ, cụ thể là "very small (3x3) convolution filters" [4]. Ý tưởng này có ý nghĩa thực tế: thay vì dùng một bộ lọc lớn ngay từ đầu, mạng xếp nhiều bộ lọc nhỏ để tăng khả năng biểu diễn nhưng vẫn giữ cấu trúc dễ hiểu. Với đồ án này, VGG16 là lựa chọn hợp lý cho phần trích xuất đặc trưng ban đầu vì kiến trúc ổn định, phổ biến và dễ kết hợp với các khối phía sau.
Trong đồ án, VGG16 không được dùng như một classifier độc lập. Mô hình chỉ sử dụng phần block tích chập của VGG16 để trích xuất đặc trưng ban đầu, sau đó đặc trưng được đưa qua Inception và Vision Transformer. Cách dùng này tận dụng khả năng học đặc trưng cục bộ của VGG16 nhưng tránh phụ thuộc hoàn toàn vào một mạng VGG đầy đủ nhiều tham số.
Hình 2.4 Kiến trúc VGG16 trong paper "Very Deep Convolutional Networks for Large-Scale Image Recognition"
Chèn hình kiến trúc VGG16 từ paper VGG [4].
2.3.3. Inception
Inception được giới thiệu trong paper "Going Deeper with Convolutions". Ý tưởng chính là xử lý cùng một đầu vào qua nhiều nhánh song song, chẳng hạn tích chập 1 x 1, 3 x 3, 5 x 5 và pooling, sau đó ghép các đầu ra theo chiều kênh [14]. Cấu trúc này giúp mô hình học đặc trưng ở nhiều tỷ lệ khác nhau. Paper Inception cũng nhấn mạnh vai trò của tích chập 1 x 1 trong việc giảm số kênh trước các phép tích chập lớn, nhờ đó giảm chi phí tính toán.
Tác giả của Inception gọi kiến trúc này là một mạng tích chập sâu có tên mã "Inception" và cho thấy nó đạt kết quả rất mạnh trong cuộc thi ImageNet năm 2014 [14]. Điểm hay của Inception không nằm ở việc làm mạng thật lớn một cách trực tiếp, mà ở cách phân bổ tính toán thông minh qua nhiều nhánh. Với ảnh da liễu, một nhánh có thể nhạy với chi tiết nhỏ, một nhánh khác nhạy với vùng rộng hơn. Khi ghép các nhánh lại, feature map chứa thông tin phong phú hơn so với việc chỉ dùng một kích thước kernel.
Với ảnh tổn thương da, đặc trưng quan trọng có thể xuất hiện ở nhiều kích thước: vùng đổi màu lớn, bờ tổn thương, chấm sắc tố nhỏ hoặc cấu trúc mạch máu. Vì vậy, ý tưởng đặc trưng đa tỷ lệ của Inception phù hợp với bài toán. Trong mô hình của đồ án, InceptionV7 được đặt sau VGG16 để làm giàu feature map trước khi đưa sang Transformer.
Hình 2.5 Inception module trong paper "Going Deeper with Convolutions"
Chèn hình Inception module gốc từ paper GoogLeNet/Inception [14].
2.4. Phát hiện vùng tổn thương bằng YOLO
2.4.1. Bài toán phát hiện đối tượng
Phát hiện đối tượng là bài toán xác định vị trí và loại đối tượng trong ảnh. Kết quả của detector gồm bounding box, điểm tin cậy và nhãn lớp. Trong đồ án, YOLO chỉ phát hiện một lớp là lesion, nghĩa là vùng tổn thương da. Detector không quyết định bệnh cuối cùng, mà cung cấp vùng quan tâm để bước phân loại tập trung vào phần ảnh có ý nghĩa.
Chỉ số quan trọng trong phát hiện đối tượng là Intersection over Union:
IoU = Area(B_pred ∩ B_gt) / Area(B_pred ∪ B_gt)
Trong đó B_pred là hộp dự đoán và B_gt là hộp ground truth. IoU càng cao thì hộp dự đoán càng khớp với vùng thật. Khi đánh giá detector, IoU được dùng để xác định một dự đoán có được tính là đúng hay không.
2.4.2. Nguyên lý YOLO
YOLO là họ mô hình phát hiện đối tượng một giai đoạn. Thay vì tạo region proposal rồi phân loại từng vùng, YOLO dự đoán trực tiếp bounding box và xác suất lớp từ ảnh đầu vào. Paper YOLO gốc mô tả ý tưởng bằng câu: "single neural network predicts bounding boxes" [2]. Cách tiếp cận này giúp YOLO có tốc độ cao và phù hợp với ứng dụng cần phản hồi nhanh.
Điểm khác biệt quan trọng của YOLO so với các phương pháp hai giai đoạn là toàn bộ quá trình phát hiện được xem như một bài toán hồi quy trực tiếp từ ảnh sang các hộp dự đoán. Với ứng dụng hỗ trợ phân tích ảnh da, điều này có lợi vì người dùng cần phản hồi trong thời gian ngắn. Mục tiêu của YOLO trong đồ án không phải phân biệt loại bệnh, mà chỉ trả lời câu hỏi: vùng nào trong ảnh có khả năng là tổn thương cần phân tích tiếp. Khi vùng này được xác định, mô hình phân loại phía sau có đầu vào tập trung hơn và ít bị nhiễu bởi nền ảnh.
YOLO hiện đại thường có ba phần: backbone để trích xuất đặc trưng, neck để kết hợp đặc trưng đa tỷ lệ, và head để dự đoán bounding box. Sau khi sinh nhiều hộp dự đoán, hệ thống dùng Non-Maximum Suppression để loại bỏ các hộp trùng lặp mạnh. Quy tắc thường dùng là giữ hộp có confidence cao nhất và loại các hộp còn lại nếu IoU với hộp đã giữ vượt ngưỡng.
Hình 2.6 Kiến trúc và cơ chế dự đoán của YOLO trong paper "You Only Look Once"
Chèn hình kiến trúc YOLO hoặc hình chia lưới dự đoán bounding box từ paper YOLO [2].
Công thức 2.1 Hàm mất mát YOLO gốc
Chèn công thức hàm mất mát YOLO từ paper "You Only Look Once" [2], gồm các thành phần localization loss, confidence loss và classification loss.
2.4.3. YOLOv8 và YOLOv11
YOLOv8 là phiên bản do Ultralytics phát triển, hỗ trợ nhiều tác vụ như phát hiện đối tượng, phân đoạn và phân loại. Theo tài liệu Ultralytics, YOLOv8 sử dụng detection head theo hướng anchor-free, giúp giảm phụ thuộc vào anchor box thiết kế thủ công [12]. Trong đồ án, YOLOv8 được triển khai bằng model yolov8s.pt.
YOLOv11 là phiên bản mới hơn trong hệ sinh thái Ultralytics. Bài tổng quan YOLOv11 mô tả các thành phần như C3k2, SPPF và C2PSA nhằm tăng khả năng trích xuất đặc trưng và cải thiện hiệu quả tính toán [3]. Tài liệu so sánh của Ultralytics cho biết YOLO11 thay thế một số module C2f bằng C3k2 và bổ sung C2PSA để tăng xử lý đặc trưng không gian [13]. Trong đồ án, YOLOv11 được triển khai bằng model yolov11s.pt.
Việc huấn luyện cả YOLOv8 và YOLOv11 giúp đồ án có cơ sở so sánh thay vì chọn detector theo cảm tính. YOLOv8 là lựa chọn ổn định, phổ biến và có hệ sinh thái tài liệu rộng. YOLOv11 mới hơn, hướng đến cải thiện hiệu quả đặc trưng và tốc độ trong cùng họ mô hình. Khi đặt hai mô hình trên cùng bộ dữ liệu ISIC 2018 đã chuyển sang nhãn bounding box, báo cáo có thể so sánh trực tiếp precision, recall và mAP để chọn detector phù hợp nhất cho pipeline.
Bảng 2.2 So sánh ngắn gọn YOLOv8 và YOLOv11 trong phạm vi đồ án
Tiêu chí	YOLOv8	YOLOv11
File model	backend/models/yolov8s.pt	backend/models/yolov11s.pt
Dữ liệu huấn luyện	ISIC 2018 Task 1 được chuyển mask sang bounding box YOLO	ISIC 2018 Task 1 được chuyển mask sang bounding box YOLO
Số lớp phát hiện	1 lớp lesion	1 lớp lesion
Vai trò	Phát hiện vùng tổn thương	Phát hiện vùng tổn thương

2.4.4. Chỉ số đánh giá detector
Khi đánh giá YOLO, các chỉ số cần quan tâm gồm precision, recall và mean Average Precision. Precision phản ánh tỷ lệ dự đoán đúng trong các hộp được mô hình phát hiện. Recall phản ánh tỷ lệ ground truth được mô hình phát hiện. mean Average Precision thường được tính dựa trên đường precision-recall ở các ngưỡng IoU khác nhau. Trong báo cáo thực nghiệm, cần trình bày mAP@0.5 và mAP@0.5:0.95 nếu có kết quả huấn luyện.
Trong bài toán của đồ án, recall của detector cần được chú ý đặc biệt. Nếu detector bỏ sót vùng tổn thương, bước phân loại phía sau có thể không nhận được vùng ảnh đúng. Ngược lại, nếu bounding box hơi rộng nhưng vẫn bao phủ tổn thương, classifier vẫn có cơ hội học được thông tin chính. Vì vậy, khi phân tích YOLO ở chương 4, nên trình bày thêm các ví dụ định tính gồm phát hiện đúng, phát hiện lệch nhẹ và bỏ sót để người đọc hiểu ý nghĩa thực tế của các con số.
Hình 2.7 Ví dụ kết quả phát hiện vùng tổn thương bằng YOLO
Chèn ảnh minh họa: ảnh da đầu vào, bounding box dự đoán, confidence score.
2.5. Mô hình phân loại lai VGG16, Inception và Vision Transformer
2.5.1. Thực trạng mô hình phân loại trên HAM10000
Các nghiên cứu trên HAM10000 thường sử dụng VGG, ResNet, Inception, Xception, DenseNet, MobileNet và EfficientNet. Nghiên cứu của Akter và cộng sự đã đánh giá nhiều mô hình trong cùng bài toán phân loại bảy lớp tổn thương da. Theo kết quả công bố, InceptionV3 đạt 90% accuracy, Xception và DenseNet đạt 88%, MobileNet đạt 87%, ResNet đạt 82%, mô hình mạng tích chập tự xây dựng đạt 77% và VGG16 đạt 77% [11]. Kết quả này cho thấy việc chọn mô hình không nên chỉ dựa vào một backbone đơn lẻ, mà cần cân bằng giữa khả năng học đặc trưng, chi phí tính toán và mục tiêu triển khai.
Ảnh da liễu cần nhận biết chi tiết cục bộ như chấm sắc tố, đường viền hoặc cấu trúc nhỏ, đồng thời cần hiểu hình dạng và phân bố màu trên toàn bộ tổn thương. Vì vậy, hướng mô hình lai là hợp lý: mạng tích chập học đặc trưng cục bộ, Inception làm giàu đặc trưng đa tỷ lệ, còn Transformer học quan hệ dài giữa các vùng đặc trưng.
Từ thực trạng này, việc lựa chọn một mô hình lai trong đồ án là có cơ sở. Nếu chỉ dùng VGG16 độc lập, mô hình có cấu trúc dễ hiểu nhưng khả năng biểu diễn có thể chưa đủ mạnh. Nếu dùng các backbone rất lớn, kết quả có thể tốt hơn nhưng chi phí huấn luyện và triển khai tăng lên. Mô hình tham khảo từ PlantXViT nằm giữa hai hướng này: vẫn dựa trên đặc trưng tích chập, nhưng thêm cơ chế chú ý của Transformer để nắm bắt quan hệ không gian rộng hơn. Điều này phù hợp với mục tiêu của đồ án là thử nghiệm, so sánh mô hình và tích hợp vào một pipeline có thể chạy được, chứ không chỉ tối ưu một chỉ số trên notebook.
2.5.2. Vision Transformer và cơ chế chú ý
Vision Transformer biểu diễn ảnh hoặc feature map thành chuỗi token rồi đưa qua Transformer Encoder. Công thức scaled dot-product attention trong Transformer là:
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V
Cơ chế này giúp mô hình học quan hệ giữa các vùng xa nhau trong ảnh. Với ảnh tổn thương da, self-attention hữu ích vì sự bất thường có thể nằm ở tương quan giữa màu sắc, bờ tổn thương và cấu trúc tổng thể. Tuy nhiên, Vision Transformer thuần thường cần nhiều dữ liệu, nên trong đồ án Transformer được đặt sau phần trích xuất đặc trưng tích chập.
Paper Vision Transformer cho thấy có thể áp dụng Transformer trực tiếp lên chuỗi các patch ảnh, với nhận định rằng một mô hình Transformer thuần xử lý "sequences of image patches" có thể đạt kết quả tốt khi được tiền huấn luyện trên lượng dữ liệu lớn [5]. Công thức biểu diễn patch embedding thường được mô tả như sau:
z_0 = [x_class; x_p^1 E; x_p^2 E; ...; x_p^N E] + E_pos
Trong đó ảnh được chia thành N patch, mỗi patch được chiếu tuyến tính thành vector đặc trưng, sau đó cộng thêm positional embedding để mô hình biết vị trí tương đối của các patch trong ảnh. Với đồ án này, Transformer không xử lý trực tiếp ảnh thô từ đầu, mà xử lý feature map đã được VGG16 và Inception trích xuất. Cách làm này giúp giảm yêu cầu dữ liệu so với Vision Transformer thuần, đồng thời vẫn tận dụng được khả năng học quan hệ toàn cục của cơ chế chú ý.
Hình 2.8 Mô hình Vision Transformer trong paper "An Image is Worth 16x16 Words"
Chèn hình tổng quan Vision Transformer từ paper ViT [5].
2.5.3. Mô hình lai tham khảo PlantXViT
Mô hình phân loại trong đồ án được tham khảo từ paper PlantXViT: "Explainable vision transformer enabled convolutional neural network for plant disease identification: PlantXViT" [10]. Đây là mô hình lai gọn nhẹ đã được áp dụng trên bài toán phân loại bệnh cây. Paper này đề xuất kết hợp mạng tích chập với Vision Transformer, có khoảng 0,8 triệu tham số huấn luyện và được thiết kế cho bối cảnh cần hiệu quả tính toán [10].
Trong đồ án, mô hình được điều chỉnh cho bảy lớp bệnh của HAM10000. Kiến trúc gồm VGG16Blocks, InceptionV7, SpatialReducer, PatchEncoder, ViTEncoder, AttentionPool và Linear classifier. VGG16Blocks học đặc trưng cục bộ; InceptionV7 làm giàu đặc trưng đa tỷ lệ; SpatialReducer giảm kích thước feature map; PatchEncoder biến feature map thành token; ViTEncoder học quan hệ giữa các token; AttentionPool tổng hợp đặc trưng; Linear classifier đưa ra tên bệnh và độ tin cậy.
Điểm cần trình bày rõ là mô hình trong đồ án không phải một mô hình hoàn toàn mới được đề xuất từ đầu. Đây là mô hình được tham khảo ý tưởng từ PlantXViT, sau đó điều chỉnh cho dữ liệu da liễu và bảy lớp của HAM10000. PlantXViT vốn được xây dựng cho bài toán bệnh cây, nhưng ý tưởng kết hợp mạng tích chập và Transformer vẫn có tính chuyển giao: cả hai bài toán đều cần nhận diện vùng bất thường trên ảnh, đều có chi tiết cục bộ và đều cần hiểu hình dạng tổng thể. Vì vậy, việc chọn mô hình này là hợp lý về mặt kỹ thuật, miễn là báo cáo trình bày rõ đây là mô hình tham khảo và đã được thay đổi cho bài toán khác.
Hình 2.9 nên thể hiện rõ luồng dữ liệu của mô hình thay vì chỉ liệt kê tên lớp. Người đọc nên nhìn thấy ảnh 224 x 224 x 3 đi vào VGG16Blocks, feature map tiếp tục qua InceptionV7, sau đó SpatialReducer giảm kích thước, PatchEncoder biến feature map thành token, ViTEncoder học quan hệ giữa các token, AttentionPool gom thông tin quan trọng và Linear classifier xuất ra bảy xác suất tương ứng bảy lớp bệnh.
Hình 2.9 Kiến trúc mô hình phân loại lai VGG16, Inception và Vision Transformer
Chèn hình kiến trúc mô hình: input 224 x 224 x 3 -> VGG16Blocks -> InceptionV7 -> SpatialReducer -> PatchEncoder -> ViTEncoder -> AttentionPool -> Linear classifier.
2.6. Truy xuất tăng cường sinh văn bản
2.6.1. Khái niệm RAG
Truy xuất tăng cường sinh văn bản là phương pháp kết hợp mô hình ngôn ngữ với kho tri thức bên ngoài. Thay vì chỉ dựa vào kiến thức nằm trong tham số của mô hình, hệ thống truy xuất các đoạn tài liệu liên quan rồi đưa vào prompt để sinh câu trả lời. Lewis và cộng sự mô tả RAG là mô hình "combine pre-trained parametric and non-parametric memory" [6]. Trong miền y tế, cách làm này giúp câu trả lời bám vào nguồn tri thức được kiểm soát hơn.
Paper RAG biểu diễn xác suất sinh câu trả lời y theo đầu vào x bằng cách biên hóa qua các tài liệu truy xuất z. Công thức khái quát có thể viết:
p(y | x) = Σ_z p_η(z | x) p_θ(y | x, z)
Trong đó p_η(z | x) là mô hình truy xuất tài liệu liên quan và p_θ(y | x, z) là mô hình sinh câu trả lời dựa trên câu hỏi và tài liệu được truy xuất [6].
Nói cách khác, RAG tách câu trả lời thành hai phần: tìm tài liệu phù hợp và sinh văn bản dựa trên tài liệu đó. Điều này đặc biệt cần thiết trong đồ án vì người dùng không chỉ cần nhãn “melanoma” hay “nevus”, mà cần một phần giải thích dễ hiểu. Nếu chỉ dùng mô hình ngôn ngữ không có truy xuất, câu trả lời có thể phụ thuộc vào kiến thức chung của mô hình và khó kiểm soát nguồn. Khi dùng RAG, hệ thống có thể giới hạn câu trả lời trong các đoạn tri thức đã chuẩn bị, từ đó giảm nguy cơ sinh thông tin không phù hợp.
Hình 2.10 Mô hình RAG trong paper "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
Chèn hình kiến trúc RAG-Sequence hoặc RAG-Token từ paper RAG [6].
2.6.2. Embedding, vector database và truy xuất ngữ nghĩa
Trong RAG, tài liệu y khoa được chia thành các đoạn nhỏ gọi là chunk. Mỗi chunk được biến đổi thành vector embedding và lưu trong vector database. Khi người dùng đặt câu hỏi, hệ thống tạo embedding cho câu hỏi rồi tìm các chunk gần nhất trong không gian vector. Độ tương đồng cosine giữa vector câu hỏi q và vector tài liệu d được tính:
cos(q, d) = (q . d) / (||q|| ||d||)
Đồ án sử dụng Chroma làm vector database và mô hình embedding đa ngôn ngữ để hỗ trợ câu hỏi tiếng Việt. Khi có kết quả phân tích ảnh, tên bệnh dự đoán được dùng như một gợi ý để truy xuất đúng phần tri thức liên quan. Đây là điểm quan trọng vì người dùng có thể hỏi bằng ngôn ngữ tự nhiên, trong khi tri thức nội bộ được tổ chức theo từng nhóm bệnh.
Embedding có thể hiểu là cách biểu diễn ý nghĩa của văn bản bằng một vector số. Hai đoạn văn có ý nghĩa gần nhau sẽ có vector gần nhau trong không gian vector, ngay cả khi chúng không dùng đúng cùng một từ. Ví dụ, câu hỏi “nốt ruồi này có nguy hiểm không” có thể được truy xuất đến các đoạn nói về dấu hiệu nghi ngờ, melanoma hoặc khuyến nghị đi khám, dù người dùng không viết đúng tên bệnh. Với tiếng Việt, việc dùng embedding đa ngôn ngữ giúp hệ thống xử lý câu hỏi tự nhiên hơn, vì người dùng thường không dùng thuật ngữ y khoa chính xác.
Trong báo cáo chính thức, nên chèn thêm một hình minh họa vector database ở mục này: tài liệu y khoa được chia thành nhiều chunk, mỗi chunk được mã hóa thành vector, truy vấn người dùng cũng được mã hóa thành vector, sau đó hệ thống lấy ra top-k chunk gần nhất để đưa vào prompt.
2.6.3. Sinh câu trả lời có ngữ cảnh
Sau khi truy xuất được ngữ cảnh y khoa, hệ thống đưa câu hỏi người dùng, tên bệnh dự đoán, tóm tắt phân tích ảnh và các đoạn tri thức liên quan vào mô hình ngôn ngữ. Mô hình sinh câu trả lời gồm triệu chứng tham khảo, nguyên nhân, hướng xử trí chung và lời khuyên đi khám khi cần. Phần prompt trong hệ thống yêu cầu trả lời bằng tiếng Việt, không bịa thông tin ngoài ngữ cảnh và luôn nhắc kết quả chỉ mang tính tham khảo.
Với bài toán y tế, phần sinh câu trả lời cần được viết thận trọng hơn chatbot thông thường. Câu trả lời không nên khẳng định “bạn bị bệnh X”, mà nên dùng cách diễn đạt như “kết quả phân tích ảnh gợi ý nhóm tổn thương X” hoặc “thông tin dưới đây chỉ mang tính tham khảo”. Đồng thời, phản hồi cần nhắc người dùng đi khám khi có dấu hiệu nguy cơ như tổn thương thay đổi nhanh, chảy máu, loét, đau, ngứa kéo dài, bờ không đều hoặc màu sắc không đồng nhất. Đây là cách thiết kế phù hợp với mục tiêu hỗ trợ, không thay thế chẩn đoán.
Hình 2.11 Quy trình RAG trong hệ thống
Chèn hình: Disease name + user prompt -> embedding -> Chroma DB -> retrieved medical context -> LLM generator -> generated response.
 
CHƯƠNG 3: PHƯƠNG PHÁP THỰC HIỆN
3.1. Quy trình thực hiện tổng quát
Đồ án được thực hiện theo hướng tập trung vào xây dựng, huấn luyện và đánh giá các mô hình học sâu cho bài toán hỗ trợ chẩn đoán bệnh da liễu từ ảnh. Phần website chỉ đóng vai trò giao diện thử nghiệm để đưa pipeline vào sử dụng, không phải trọng tâm chính của đồ án. Quy trình thực hiện gồm bốn nhóm công việc chính: chuẩn bị dữ liệu phát hiện vùng tổn thương, chuẩn bị dữ liệu phân loại bệnh, huấn luyện các mô hình, và kết hợp các mô hình vào pipeline suy luận hoàn chỉnh.
Pipeline suy luận cuối cùng nhận ảnh đầu vào, kiểm tra ảnh có phải ảnh da hay không, phát hiện vùng tổn thương bằng YOLO, phân loại bệnh bằng mô hình lai VGG16, Inception và Vision Transformer, sau đó kết hợp tên bệnh với cơ sở tri thức y khoa để sinh phản hồi tham khảo bằng tiếng Việt. Cách tổ chức này giúp tách rõ hai nhiệm vụ thị giác máy tính: phát hiện vùng bệnh và phân loại bệnh.
Khi trình bày chương phương pháp, điều quan trọng là người đọc phải hiểu được đồ án được làm theo một chuỗi công việc có kiểm chứng, không phải chỉ lấy mô hình có sẵn rồi chạy thử. Vì vậy, chương này nên cho thấy rõ ba lớp công việc. Lớp thứ nhất là chuẩn bị dữ liệu: tạo nhãn YOLO từ mask, chia tập dữ liệu, kiểm tra phân bố lớp và tiền xử lý ảnh. Lớp thứ hai là huấn luyện mô hình: thử nghiệm detector, huấn luyện classifier, theo dõi loss và chỉ số đánh giá. Lớp thứ ba là tích hợp pipeline: đưa kết quả thị giác máy tính vào hệ thống hỏi đáp có truy xuất tri thức. Cách trình bày này giúp người đọc chưa biết source code vẫn nắm được đồ án đi từ dữ liệu đến mô hình rồi đến ứng dụng.
Hình 3.1 Quy trình thực hiện tổng quát của đồ án
Chèn hình quy trình: chuẩn bị dữ liệu YOLO -> huấn luyện YOLOv8/YOLOv11 -> chuẩn bị HAM10000 -> huấn luyện classifier -> tích hợp RAG -> thử nghiệm pipeline.
Hình 3.1 nên vẽ theo dạng luồng hai nhánh: nhánh phát hiện dùng ISIC 2018 Task 1 để huấn luyện YOLO, nhánh phân loại dùng HAM10000 để huấn luyện classifier. Hai nhánh gặp nhau ở pipeline suy luận. Cách vẽ này tránh hiểu nhầm rằng YOLO và classifier cùng được huấn luyện trên một bộ dữ liệu.
3.1.1. Quy trình huấn luyện mô hình
Quy trình huấn luyện được chia thành hai nhánh. Nhánh phát hiện vùng tổn thương sử dụng ISIC 2018 Task 1, trong đó mask phân đoạn ground truth được chuyển sang bounding box để huấn luyện YOLO. Nhánh phân loại bệnh sử dụng HAM10000, gồm bảy lớp bệnh da liễu. Hai nhánh này độc lập ở giai đoạn huấn luyện nhưng được kết hợp ở giai đoạn suy luận.
3.1.2. Quy trình suy luận của hệ thống
Ở giai đoạn suy luận, ảnh đầu vào trước hết được kiểm tra bằng module phát hiện ảnh da. Nếu ảnh không đạt ngưỡng pixel da, pipeline dừng và trả cảnh báo. Nếu ảnh hợp lệ, YOLO phát hiện vùng tổn thương. Vùng ảnh được phát hiện hoặc toàn ảnh tùy cấu hình được đưa vào classifier để dự đoán bệnh. Kết quả phân loại gồm tên bệnh và độ tin cậy, sau đó được đưa vào pipeline RAG để truy xuất tri thức và sinh phản hồi.
3.2. Chuẩn bị dữ liệu phát hiện tổn thương
3.2.1. Bộ dữ liệu ISIC 2018 Task 1
Dữ liệu dùng để huấn luyện YOLO được lấy từ ISIC 2018 Challenge Task 1: Lesion Boundary Segmentation. Đây là bộ dữ liệu có ảnh tổn thương da kèm mask ground truth, phù hợp để xây dựng nhãn bounding box cho bài toán phát hiện vùng tổn thương. Việc sử dụng bộ dữ liệu có ground truth giúp detector học vị trí tổn thương rõ ràng hơn so với việc cố tạo nhãn từ HAM10000, vốn là bộ dữ liệu chủ yếu phục vụ phân loại.
Trong notebook yolo_dataset_labeling.ipynb, dữ liệu được tải từ Kaggle dataset tschandl/isic2018-challenge-task1-data-segmentation. Sau khi giải nén, thư mục dữ liệu gồm ảnh đầu vào và thư mục mask ground truth ISIC2018_Task1_Training_GroundTruth.
Lý do chọn ISIC 2018 Task 1 cho YOLO là bộ dữ liệu này có mask phân đoạn tổn thương. Mask cho biết vùng tổn thương thật nằm ở đâu trên ảnh, từ đó có thể chuyển sang bounding box để huấn luyện mô hình phát hiện. Đây là điểm khác với HAM10000: HAM10000 có nhãn bệnh cho toàn ảnh nhưng không cung cấp sẵn bounding box của vùng bệnh. Nếu dùng HAM10000 để huấn luyện YOLO mà không có ground truth vị trí, nhãn phát hiện sẽ thiếu cơ sở. Vì vậy, trong đồ án, ISIC 2018 phục vụ bài toán định vị tổn thương, còn HAM10000 phục vụ bài toán phân loại bệnh.
Hình 3.2 nên minh họa rõ sự khác nhau giữa ảnh gốc, mask và bounding box. Người đọc chỉ cần nhìn hình này là hiểu vì sao mask phân đoạn có thể chuyển thành nhãn YOLO.
3.2.2. Chuyển mask phân đoạn sang bounding box
Mỗi ảnh trong tập ISIC 2018 có một file mask tương ứng với hậu tố _segmentation.png. Mask được đọc dưới dạng ảnh xám, sau đó được nhị phân hóa bằng ngưỡng 127. Từ mask nhị phân, thuật toán tìm các contour ngoài và chọn contour có diện tích lớn nhất làm vùng tổn thương chính. Bounding box được tạo bằng hàm cv2.boundingRect, trả về tọa độ góc trái trên, chiều rộng và chiều cao của vùng bao quanh tổn thương.
Quy trình này có thể xem như một bước chuyển đổi bài toán: từ phân đoạn sang phát hiện đối tượng. Phân đoạn mô tả vùng tổn thương ở mức pixel, còn YOLO cần nhãn dạng hộp chữ nhật. Việc chọn contour lớn nhất phù hợp với giả định mỗi ảnh trong tập dữ liệu có một tổn thương chính. Sau khi tạo hộp, tọa độ được chuẩn hóa theo kích thước ảnh để mô hình có thể học ổn định trên ảnh có kích thước khác nhau.
Hình 3.2 Minh họa chuyển mask phân đoạn sang bounding box
Chèn hình gồm ảnh gốc, mask ground truth và bounding box màu đỏ tạo từ contour lớn nhất.
Hình bổ sung đề xuất: chèn thêm 4 đến 6 ảnh kiểm tra label sau khi sinh nhãn, gồm các trường hợp tổn thương lớn, nhỏ, lệch khỏi trung tâm và có màu nền da khác nhau. Đây là bằng chứng trực quan cho thấy bước tạo label hoạt động đúng.
3.2.3. Tạo nhãn theo định dạng YOLO
Sau khi có bounding box dạng pixel, nhãn được chuyển sang định dạng YOLO. Mỗi file nhãn có một dòng:
0 x_center y_center width height
Trong đó 0 là mã lớp duy nhất, tương ứng với lớp lesion. Bốn giá trị còn lại được chuẩn hóa về khoảng [0, 1] theo kích thước ảnh. Gọi kích thước ảnh là W x H, bounding box có góc trái trên là (x, y), chiều rộng w và chiều cao h:
x_center = (x + w / 2) / W
y_center = (y + h / 2) / H
width = w / W
height = h / H
Bảng 3.1 Định dạng nhãn YOLO sử dụng trong đồ án
Thành phần	Ý nghĩa
class_id	Mã lớp phát hiện, trong đồ án chỉ có lớp 0 tương ứng lesion
x_center	Tọa độ tâm theo trục ngang, đã chuẩn hóa theo chiều rộng ảnh
y_center	Tọa độ tâm theo trục dọc, đã chuẩn hóa theo chiều cao ảnh
width	Chiều rộng bounding box, đã chuẩn hóa
height	Chiều cao bounding box, đã chuẩn hóa

3.2.4. Chia tập train, validation và test
Dữ liệu được chia thành ba tập train, validation và test theo tỷ lệ 70%, 15% và 15%. Kết quả xử lý trong notebook cho thấy toàn bộ 2594 ảnh đều được tạo label thành công. Cấu trúc thư mục sau xử lý tuân theo định dạng phổ biến của YOLO, gồm images/train, images/val, images/test, labels/train, labels/val và labels/test.
Bảng 3.2 Thống kê dữ liệu huấn luyện YOLO
Tập dữ liệu	Số ảnh	Số label tạo thành công
Train	1815	1815
Validation	389	389
Test	390	390
Tổng cộng	2594	2594

3.2.5. Kiểm tra trực quan nhãn bounding box
Sau khi tạo label, notebook có bước hiển thị ảnh train kèm bounding box màu đỏ để kiểm tra trực quan. Bước này quan trọng vì nếu mask bị đọc sai, contour bị chọn sai hoặc tọa độ chuẩn hóa không đúng, mô hình YOLO sẽ học sai vị trí tổn thương. Kiểm tra trực quan giúp phát hiện sớm lỗi trong quá trình sinh nhãn.
Trong báo cáo chính thức, nên trình bày một hình lưới gồm nhiều ảnh có bounding box để chứng minh nhãn được tạo hợp lý. Ngoài ra, có thể bổ sung một biểu đồ histogram diện tích bounding box theo tỷ lệ diện tích ảnh. Biểu đồ này giúp đánh giá tổn thương thường chiếm bao nhiêu phần trăm ảnh và có trường hợp bounding box quá nhỏ hoặc quá lớn bất thường hay không. Nếu có nhiều bounding box quá nhỏ, YOLO có thể khó học; nếu nhiều hộp gần bằng toàn ảnh, bước crop có thể không cải thiện nhiều so với dùng ảnh gốc.
3.3. Chuẩn bị dữ liệu phân loại bệnh
3.3.1. Bộ dữ liệu HAM10000
Dữ liệu phân loại sử dụng HAM10000, gồm bảy lớp: akiec, bcc, bkl, df, mel, nv và vasc. Theo notebook huấn luyện, dữ liệu đã được chia thành train, validation và test. Tập train gồm 7010 ảnh, tập validation gồm 1502 ảnh và tập test gồm 1503 ảnh. Ảnh được đọc từ hai thư mục HAM10000_images_part_1 và HAM10000_images_part_2.
Khi trình bày dữ liệu phân loại, cần giải thích rõ ý nghĩa của việc chia train, validation và test. Tập train dùng để mô hình học tham số. Tập validation dùng để theo dõi quá trình huấn luyện và chọn checkpoint tốt. Tập test chỉ dùng ở cuối để đánh giá khách quan hơn. Nếu dùng test trong quá trình chọn mô hình, kết quả sẽ dễ bị lạc quan quá mức. Vì vậy, báo cáo nên nhấn mạnh rằng các chỉ số cuối cùng ở chương 4 được lấy trên tập test gồm 1503 ảnh.
Bảng 3.3 Thống kê tập dữ liệu HAM10000 dùng cho phân loại
Tập dữ liệu	Số ảnh
Train	7010
Validation	1502
Test	1503
Tổng cộng	10015

3.3.2. Tiền xử lý ảnh
Ảnh đầu vào được đưa về kích thước 224 x 224 để phù hợp với kiến trúc VGG16 và mô hình lai được tham khảo từ PlantXViT. Với mô hình PyTorch, ảnh được chuẩn hóa theo mean [0.485, 0.456, 0.406] và std [0.229, 0.224, 0.225], tương ứng cách chuẩn hóa phổ biến khi dùng backbone từ ImageNet.
Đối với tập train, đồ án sử dụng các phép tăng cường dữ liệu như RandomResizedCrop, lật ngang, lật dọc, xoay ảnh và ColorJitter. Đối với tập validation và test, ảnh chỉ được resize và chuẩn hóa, không dùng augmentation để đảm bảo đánh giá ổn định.
3.3.3. Xử lý mất cân bằng dữ liệu
HAM10000 có phân bố lớp mất cân bằng rõ rệt. Trong tập train, lớp nv chiếm số lượng lớn nhất với 4693 ảnh, trong khi df chỉ có 81 ảnh và vasc có 99 ảnh. Nếu huấn luyện trực tiếp, mô hình dễ thiên về lớp lớn và bỏ sót lớp nhỏ. Vì vậy, đồ án sử dụng các kỹ thuật xử lý mất cân bằng như class weight, WeightedRandomSampler và CB-Focal Loss.
Phần này nên có một biểu đồ cột phân bố lớp trong tập train. Biểu đồ sẽ làm nổi bật ngay vấn đề mất cân bằng: lớp nv áp đảo so với df và vasc. Đây là cơ sở trực quan để thuyết phục người đọc rằng việc dùng WeightedRandomSampler và CB-Focal Loss là cần thiết, không phải là lựa chọn tùy ý.
Bảng 3.4 Phân bố lớp trong tập train HAM10000
Lớp	Số ảnh train
akiec	229
bcc	360
bkl	769
df	81
mel	779
nv	4693
vasc	99

3.3.4. Tăng cường dữ liệu
Tăng cường dữ liệu giúp mô hình ổn định hơn trước các biến đổi thường gặp trong ảnh da liễu như góc chụp, vị trí tổn thương, độ sáng và độ tương phản. Các phép tăng cường được sử dụng gồm cắt ngẫu nhiên có resize, lật ngang, lật dọc, xoay ảnh và thay đổi nhẹ độ sáng, độ tương phản, độ bão hòa. Mục tiêu là tăng tính đa dạng của tập train nhưng không làm biến dạng bản chất tổn thương.
Tăng cường dữ liệu trong ảnh da liễu cần được dùng cẩn thận. Các phép biến đổi như lật, xoay hoặc thay đổi nhẹ độ sáng thường hợp lý vì ảnh tổn thương có thể được chụp ở nhiều hướng khác nhau. Tuy nhiên, các phép biến đổi quá mạnh có thể làm sai lệch màu sắc hoặc cấu trúc tổn thương, từ đó tạo ra mẫu huấn luyện không còn giống dữ liệu thật. Vì vậy, báo cáo nên trình bày augmentation như một biện pháp tăng độ bền của mô hình, không phải cách tạo thêm dữ liệu tùy tiện.
Hình 3.3 Ví dụ tăng cường dữ liệu trên ảnh HAM10000
Chèn hình gồm một ảnh gốc và một số biến thể sau augmentation.
Hình 3.3 nên chọn một ảnh dễ quan sát, sau đó đặt cạnh các biến thể sau augmentation. Chú thích cần nói rõ các biến thể vẫn giữ nguyên nhãn bệnh vì chỉ thay đổi góc nhìn, vùng cắt và ánh sáng ở mức vừa phải.
3.4. Xây dựng mô hình phát hiện tổn thương
3.4.1. Huấn luyện YOLOv8
YOLOv8 được huấn luyện trên tập dữ liệu ISIC 2018 đã chuyển sang định dạng YOLO. Mô hình sử dụng một lớp phát hiện duy nhất là lesion. Sau huấn luyện, trọng số tốt nhất được lưu vào file yolov8s.pt và được khai báo trong model_registry.json với tên detector yolo8s_best.
Trong báo cáo, phần YOLOv8 nên ghi rõ lệnh huấn luyện hoặc bảng cấu hình huấn luyện gồm kích thước ảnh, số epoch, batch size, optimizer, learning rate và thiết bị huấn luyện. Sau khi có log huấn luyện, nên chèn biểu đồ train loss, validation loss, precision, recall và mAP theo epoch. Các biểu đồ này giúp người đọc thấy mô hình có học ổn định hay không, có dấu hiệu quá khớp hay không và checkpoint tốt nhất xuất hiện ở giai đoạn nào.
3.4.2. Huấn luyện YOLOv11
Tương tự YOLOv8, YOLOv11 được huấn luyện trên cùng tập dữ liệu phát hiện tổn thương. Việc huấn luyện cả YOLOv8 và YOLOv11 cho phép so sánh hai phiên bản detector trong cùng điều kiện dữ liệu. Trọng số tốt nhất của YOLOv11 được lưu vào file yolov11s.pt và được khai báo với tên detector yolo11s_best.
YOLOv11 cần được trình bày song song với YOLOv8 để so sánh công bằng. Nếu hai mô hình dùng cùng tập train, validation và test, cùng kích thước ảnh và cùng số epoch, sự khác biệt trong kết quả có thể được quy về kiến trúc và quá trình tối ưu của từng phiên bản. Nếu cấu hình huấn luyện khác nhau, báo cáo cần ghi rõ để tránh kết luận thiếu cơ sở.
3.4.3. Lựa chọn checkpoint tốt nhất
Trong quá trình huấn luyện detector, checkpoint tốt nhất cần được lựa chọn dựa trên kết quả validation, đặc biệt là mAP, precision và recall. Với bài toán phát hiện tổn thương da, recall có ý nghĩa quan trọng vì bỏ sót vùng tổn thương sẽ ảnh hưởng trực tiếp đến bước phân loại phía sau.
Ngoài chỉ số định lượng, checkpoint detector nên được kiểm tra bằng ảnh dự đoán thực tế. Báo cáo nên có một hình gồm ba nhóm ví dụ: phát hiện đúng, phát hiện chưa sát nhưng vẫn bao phủ tổn thương, và phát hiện sai hoặc bỏ sót. Nhóm ví dụ này giúp người đọc hiểu rằng một detector có mAP cao vẫn có thể gặp lỗi ở một số ảnh khó, đặc biệt khi tổn thương nhỏ, màu gần với nền da hoặc ảnh có ánh sáng không đều.
Bảng 3.5 Cấu hình huấn luyện detector cần trình bày
Thông số	YOLOv8	YOLOv11
Dataset	ISIC 2018 Task 1	ISIC 2018 Task 1
Số lớp	1	1
Kích thước ảnh	[Điền]	[Điền]
Số epoch	[Điền]	[Điền]
Batch size	[Điền]	[Điền]
Optimizer	[Điền]	[Điền]
Checkpoint tốt nhất	yolov8s.pt	yolov11s.pt

3.5. Xây dựng mô hình phân loại bệnh
3.5.1. Kiến trúc mô hình lai
Mô hình phân loại chính được tham khảo từ PlantXViT, sau đó điều chỉnh cho bài toán phân loại bảy lớp tổn thương da. Kiến trúc gồm các thành phần: VGG16Blocks, InceptionV7, SpatialReducer, PatchEncoder, ViTEncoder, AttentionPool và Linear classifier. VGG16Blocks trích xuất đặc trưng cục bộ, InceptionV7 làm giàu đặc trưng đa tỷ lệ, ViTEncoder học quan hệ giữa các vùng đặc trưng và AttentionPool tổng hợp đặc trưng trước khi phân loại.
Để người đọc dễ hình dung, nên trình bày kiến trúc theo luồng dữ liệu thay vì chỉ liệt kê tên module. Ảnh đầu vào kích thước 224 x 224 x 3 đi qua VGG16Blocks để tạo feature map cục bộ. Feature map này tiếp tục qua InceptionV7 để thu thêm đặc trưng ở nhiều tỷ lệ. SpatialReducer giảm kích thước không gian để số token không quá lớn. PatchEncoder chuyển feature map thành chuỗi token. ViTEncoder học quan hệ giữa các token. AttentionPool chọn lọc và gom thông tin quan trọng trước khi Linear classifier đưa ra xác suất của bảy lớp bệnh.
Hình 3.4 Kiến trúc mô hình phân loại lai
Chèn hình kiến trúc VGG16Blocks -> InceptionV7 -> SpatialReducer -> PatchEncoder -> ViTEncoder -> AttentionPool -> Linear classifier.
3.5.2. Cấu hình huấn luyện
Notebook train_vgg_inception_vit_cbfocal.ipynb sử dụng ảnh kích thước 224, batch size train 24, batch size eval 32, số lớp là 7. Quá trình huấn luyện gồm hai phase. Phase 1 đóng băng VGG backbone và huấn luyện các khối phía sau trong 18 epoch với learning rate 3e-4. Phase 2 mở toàn bộ mô hình và fine-tune trong 12 epoch với differential learning rate, trong đó learning rate của backbone nhỏ hơn phần head.
Huấn luyện hai phase giúp mô hình ổn định hơn. Ở phase đầu, backbone VGG được đóng băng để các khối mới như Inception, Transformer và classifier học cách sử dụng đặc trưng có sẵn. Ở phase sau, toàn bộ mô hình được mở để tinh chỉnh đồng bộ trên dữ liệu HAM10000. Differential learning rate được dùng vì backbone tiền huấn luyện cần thay đổi chậm hơn, trong khi các tầng mới cần học nhanh hơn.
Bảng 3.6 Cấu hình huấn luyện classifier chính
Thông số	Giá trị
Kích thước ảnh	224 x 224
Số lớp	7
Batch size train	24
Batch size eval	32
Phase 1 epochs	18
Phase 2 epochs	12
Optimizer	AdamW
Weight decay	1e-4
Warmup ratio	0.1
Gradient clipping	1.0
Mixed precision	Có sử dụng nếu GPU hỗ trợ

3.5.3. Hàm mất mát và thuật toán tối ưu
Để xử lý mất cân bằng dữ liệu, mô hình sử dụng CB-Focal Loss. Class-Balanced Loss điều chỉnh trọng số theo số mẫu hiệu dụng của từng lớp, còn Focal Loss tập trung hơn vào các mẫu khó phân loại. Kết hợp hai ý tưởng này giúp mô hình chú ý nhiều hơn đến các lớp hiếm và các mẫu khó, thay vì chỉ học tốt lớp chiếm đa số.
Optimizer được sử dụng là AdamW, một biến thể tách weight decay khỏi bước cập nhật gradient để regularization ổn định hơn so với cách đưa trực tiếp weight decay vào Adam [19]. Quá trình huấn luyện kết hợp lịch learning rate cosine với warmup. Warmup giúp quá trình huấn luyện ổn định ở giai đoạn đầu, còn cosine schedule giúp learning rate giảm dần mượt hơn trong quá trình huấn luyện.
Chương 3 nên chèn thêm hình đường cong loss và macro-F1 theo epoch của classifier. Nếu training loss giảm nhưng validation loss tăng, đó là dấu hiệu quá khớp. Nếu macro-F1 tăng chậm hơn accuracy, điều đó phản ánh mô hình vẫn đang gặp khó với các lớp ít mẫu. Những nhận xét này làm phần kết quả chương 4 thuyết phục hơn vì người đọc thấy được quá trình học, không chỉ thấy một con số cuối cùng.
3.6. Xây dựng pipeline suy luận
3.6.1. Kiểm tra ảnh đầu vào
Trước khi chạy mô hình học sâu, ảnh đầu vào được kiểm tra định dạng, kích thước và tỷ lệ pixel da. Nếu ảnh không phải ảnh da, pipeline dừng sớm và trả cảnh báo. Bước này giúp tránh trường hợp hệ thống đưa ra kết quả bệnh da liễu cho ảnh không liên quan.
Đây là một bước nhỏ nhưng có ý nghĩa thực tế. Trong ứng dụng mở cho người dùng, không thể giả định mọi ảnh tải lên đều là ảnh da. Người dùng có thể gửi ảnh nền, ảnh vật thể, ảnh quá tối hoặc ảnh không liên quan. Nếu hệ thống vẫn cố phân loại, kết quả trả về sẽ gây hiểu nhầm. Vì vậy, module kiểm tra ảnh đầu vào đóng vai trò như một lớp bảo vệ trước khi chạy detector và classifier.
3.6.2. Phát hiện và phân loại bệnh
Nếu ảnh hợp lệ, YOLO phát hiện vùng tổn thương. Detection có độ tin cậy thấp hơn ngưỡng bị loại bỏ. Nếu có nhiều detection hợp lệ, hệ thống chọn vùng tốt nhất dựa trên độ tin cậy và diện tích. Sau đó classifier dự đoán tên bệnh và độ tin cậy. Kết quả này được chuẩn hóa thành summary để đưa sang bước RAG.
Trong phần này nên chèn hình minh họa một ảnh đầu vào đi qua từng bước: ảnh gốc, ảnh có bounding box, ảnh crop vùng tổn thương, bảng xác suất bảy lớp và nhãn cuối cùng. Hình này giúp người đọc thấy rõ kết quả của từng mô hình trong pipeline, thay vì chỉ thấy giao diện cuối.
3.6.3. Kết hợp kết quả phân loại với RAG
Tên bệnh dự đoán và câu hỏi người dùng được đưa vào pipeline RAG. Hệ thống truy xuất các đoạn tri thức liên quan trong vector database rồi sinh phản hồi bằng tiếng Việt. Câu trả lời có thể gồm thông tin về triệu chứng, nguyên nhân, hướng xử trí tham khảo và lời khuyên đi khám.
Đầu vào của RAG không chỉ là câu hỏi người dùng, mà còn có kết quả phân tích ảnh. Ví dụ, nếu classifier dự đoán lớp bcc với độ tin cậy cao, hệ thống có thể ưu tiên truy xuất các đoạn tri thức liên quan đến basal cell carcinoma. Nhờ vậy, câu trả lời có ngữ cảnh hơn so với việc chỉ trả lời câu hỏi chung chung. Tuy nhiên, prompt cần luôn yêu cầu mô hình ngôn ngữ diễn đạt thận trọng, không khẳng định chẩn đoán và không bịa thông tin ngoài ngữ cảnh được truy xuất.
Hình 3.5 Pipeline suy luận hoàn chỉnh
Chèn hình: kiểm tra ảnh da -> YOLO -> classifier -> disease name -> RAG -> generated response.
Hình bổ sung đề xuất: chèn một ảnh chụp màn hình giao diện chat sau khi phân tích ảnh thành công, trong đó có ảnh đầu vào, vùng tổn thương được đánh dấu, tên bệnh dự đoán, độ tin cậy và câu trả lời tiếng Việt. Đây là bằng chứng cho thấy pipeline đã được tích hợp vào ứng dụng, dù phần website không phải trọng tâm chính.
3.7. Triển khai giao diện thử nghiệm
3.7.1. Màn hình chat
Giao diện chat cho phép người dùng gửi ảnh và nhập câu hỏi. Khi ảnh được gửi, frontend gọi API phân tích ảnh, hiển thị kết quả bounding box và tóm tắt phân loại. Sau đó hệ thống tiếp tục gọi API hội thoại để sinh câu trả lời dựa trên RAG. Đây là giao diện thử nghiệm cho pipeline, không phải trọng tâm nghiên cứu chính của đồ án.
Trong báo cáo, chỉ cần trình bày ngắn gọn giao diện chat như môi trường chạy thử pipeline. Không nên dành quá nhiều dung lượng cho thiết kế web, vì trọng tâm của đồ án là huấn luyện, đánh giá và so sánh mô hình. Tuy nhiên, nên có một hình giao diện để chứng minh kết quả mô hình đã được đưa vào hệ thống sử dụng được.
3.7.2. Màn hình quản trị mô hình
Màn hình quản trị cho phép chọn detector, classifier và chế độ đầu vào cho classifier. Chức năng này giúp thử nghiệm nhiều pipeline khác nhau, ví dụ YOLOv8 kết hợp classifier chính hoặc YOLOv11 kết hợp classifier chính, mà không cần sửa trực tiếp mã nguồn.
Màn hình quản trị nên được trình bày như công cụ hỗ trợ thực nghiệm. Nhờ màn hình này, người thực hiện có thể đổi detector, đổi classifier hoặc đổi chế độ crop/toàn ảnh để quan sát ảnh hưởng đến pipeline. Đây là phần phục vụ nghiên cứu mô hình, không cần mô tả sâu như một hệ thống quản trị hoàn chỉnh.

CHƯƠNG 4: THỰC NGHIỆM VÀ ĐÁNH GIÁ
4.1. Thiết lập thực nghiệm
4.1.1. Môi trường thực nghiệm
Các thí nghiệm huấn luyện mô hình được thực hiện chủ yếu trên Google Colab và Google Drive để lưu dữ liệu, checkpoint và kết quả. Dữ liệu YOLO được xử lý trong notebook yolo_dataset_labeling.ipynb; mô hình phân loại chính được huấn luyện trong notebook train_vgg_inception_vit_cbfocal.ipynb và các notebook thử nghiệm liên quan như VGG16+Inception+ViT_v4.ipynb.
4.1.2. Cấu hình phần cứng và thư viện
Mô hình được triển khai bằng PyTorch cho classifier chính, OpenCV cho xử lý mask và bounding box, Ultralytics cho YOLO, scikit-learn cho các chỉ số đánh giá, Matplotlib và Seaborn cho biểu đồ. Khi GPU khả dụng, notebook sử dụng mixed precision để tăng tốc huấn luyện và giảm tiêu thụ bộ nhớ.
4.1.3. Các chỉ số đánh giá
Với mô hình phát hiện vùng tổn thương, các chỉ số đánh giá gồm precision, recall, mAP@0.5 và mAP@0.5:0.95. Với mô hình phân loại bệnh, các chỉ số gồm accuracy, precision, recall, F1-score, macro-F1, weighted-F1, balanced accuracy và ma trận nhầm lẫn. Macro-F1 đặc biệt quan trọng vì dữ liệu HAM10000 bị mất cân bằng giữa các lớp.
Bảng 4.1 Các chỉ số đánh giá sử dụng trong đồ án
Nhóm mô hình	Chỉ số đánh giá
YOLO detector	Precision, recall, mAP@0.5, mAP@0.5:0.95
Classifier	Accuracy, precision, recall, F1-score, macro-F1, confusion matrix
Pipeline hoàn chỉnh	Kết quả ảnh minh họa, độ hợp lý của phản hồi RAG, thời gian xử lý

4.2. Kết quả phát hiện tổn thương
4.2.1. Kết quả YOLOv8
YOLOv8 được huấn luyện trên tập dữ liệu ISIC 2018 Task 1 đã chuyển mask sang bounding box. Do notebook hiện tại chủ yếu thể hiện bước chuẩn bị dữ liệu và tạo label, phần kết quả huấn luyện cần bổ sung từ log huấn luyện YOLOv8 sau khi chạy train. Các chỉ số cần ghi gồm precision, recall, mAP@0.5 và mAP@0.5:0.95.
4.2.2. Kết quả YOLOv11
YOLOv11 được huấn luyện trên cùng dữ liệu với YOLOv8 để đảm bảo điều kiện so sánh công bằng. Tương tự YOLOv8, cần bổ sung bảng kết quả từ log huấn luyện YOLOv11. Nếu YOLOv11 có mAP hoặc recall cao hơn YOLOv8, có thể chọn YOLOv11 làm detector mặc định; nếu chênh lệch không lớn nhưng YOLOv8 nhanh hơn, cần cân nhắc giữa tốc độ và độ chính xác.
4.2.3. So sánh YOLOv8 và YOLOv11
Bảng 4.2 Kết quả so sánh YOLOv8 và YOLOv11
Mô hình	Precision	Recall	mAP@0.5	mAP@0.5:0.95	Nhận xét
YOLOv8s	[Điền]	[Điền]	[Điền]	[Điền]	[Điền]
YOLOv11s	[Điền]	[Điền]	[Điền]	[Điền]	[Điền]

Hình 4.1 Biểu đồ kết quả huấn luyện YOLOv8
Chèn biểu đồ loss, precision, recall, mAP của YOLOv8.
Hình 4.2 Biểu đồ kết quả huấn luyện YOLOv11
Chèn biểu đồ loss, precision, recall, mAP của YOLOv11.
4.2.4. Nhận xét kết quả phát hiện
Kết quả phát hiện cần được nhận xét theo hai hướng: định lượng và định tính. Về định lượng, so sánh mAP, precision và recall giữa YOLOv8 và YOLOv11. Về định tính, cần chèn một số ảnh phát hiện đúng, ảnh phát hiện lệch vùng tổn thương và ảnh detector bỏ sót. Với bài toán này, trường hợp bỏ sót vùng tổn thương thường nghiêm trọng hơn trường hợp bounding box hơi rộng, vì nếu detector không tìm thấy vùng bệnh thì classifier có thể không nhận được đầu vào phù hợp.
4.3. Kết quả phân loại bệnh
4.3.1. Kết quả huấn luyện mô hình phân loại
Mô hình phân loại lai VGG16, Inception và Vision Transformer được đánh giá trên tập test gồm 1503 ảnh. Theo kết quả từ notebook VGG16+Inception+ViT_v4.ipynb, mô hình đạt test loss 0,7857, accuracy 0,876 và macro-F1 0,749. Đây là kết quả tương đối tốt trong bối cảnh dữ liệu HAM10000 bị mất cân bằng lớp mạnh.
Bảng 4.3 Kết quả tổng quát của mô hình phân loại chính
Chỉ số	Giá trị
Test loss	0,7857
Test accuracy	0,876
Test macro-F1	0,749
Số ảnh test	1503

Hình 4.3 Đường cong loss và accuracy trong quá trình huấn luyện classifier
Chèn biểu đồ train loss, validation loss, train accuracy và validation accuracy.
4.3.2. Precision, recall và F1-score theo từng lớp
Bảng 4.4 Classification report của mô hình phân loại chính
Lớp	Precision	Recall	F1-score	Support
akiec	0,65	0,73	0,69	49
bcc	0,76	0,84	0,80	77
bkl	0,76	0,75	0,75	165
df	0,58	0,41	0,48	17
mel	0,79	0,57	0,66	167
nv	0,93	0,96	0,94	1006
vasc	1,00	0,82	0,90	22
Macro avg	0,78	0,73	0,75	1503
Weighted avg	0,87	0,88	0,87	1503

Kết quả cho thấy mô hình dự đoán rất tốt lớp nv, vốn là lớp có số lượng lớn nhất. Lớp vasc có precision cao nhưng support nhỏ, nên cần thận trọng khi diễn giải. Lớp df có F1-score thấp nhất do số lượng mẫu ít và có thể bị nhầm với các tổn thương lành tính khác. Lớp mel đạt precision 0,79 nhưng recall 0,57, cho thấy vẫn còn trường hợp melanoma bị dự đoán sang lớp khác. Đây là hạn chế quan trọng cần nhấn mạnh vì melanoma là lớp có ý nghĩa lâm sàng cao.
4.3.3. Ma trận nhầm lẫn
Bảng 4.5 Ma trận nhầm lẫn của mô hình phân loại chính
True \\ Pred	akiec	bcc	bkl	df	mel	nv	vasc
akiec	36	2	8	0	2	1	0
bcc	3	65	2	2	1	4	0
bkl	9	7	124	0	8	17	0
df	0	2	1	7	1	6	0
mel	5	2	16	0	96	48	0
nv	2	6	13	2	13	970	0
vasc	0	1	0	1	1	1	18

Hình 4.4 Ma trận nhầm lẫn trực quan
Chèn heatmap confusion matrix từ notebook.
4.3.4. Phân tích các lớp dễ nhầm lẫn
Từ ma trận nhầm lẫn, melanoma bị nhầm nhiều sang nv và bkl. Đây là hiện tượng hợp lý về mặt hình ảnh vì các tổn thương sắc tố có thể có màu sắc hoặc hình dạng tương đối giống nhau. Lớp df cũng bị nhầm sang nv, một phần do số lượng mẫu test của df chỉ có 17 ảnh. Các lớp có ít mẫu cần được cải thiện bằng cách bổ sung dữ liệu, tăng cường dữ liệu có kiểm soát hoặc sử dụng loss function phù hợp hơn.
4.4. So sánh các mô hình phân loại
4.4.1. Các mô hình đã thử nghiệm
Trong quá trình thực hiện, đồ án có nhiều notebook thử nghiệm như CNN baseline, VGG16 + Inception + ViT và ConvNeXt + Swin Attention. Các mô hình này giúp đánh giá nhiều hướng tiếp cận khác nhau: mô hình CNN nhẹ, mô hình lai dựa trên VGG16 và Transformer, cũng như hướng dùng backbone hiện đại hơn.
4.4.2. Bảng so sánh kết quả
Bảng 4.6 So sánh các mô hình phân loại đã thử nghiệm
Mô hình	Accuracy	Macro-F1	Ghi chú
CNN baseline	[Điền]	[Điền]	Mô hình cơ sở, kiến trúc đơn giản
VGG16 + Inception	[Điền]	[Điền]	Thử nghiệm đặc trưng tích chập và đa tỷ lệ
VGG16 + Inception + Vision Transformer	0,876	0,749	Mô hình chính
ConvNeXt + Swin Attention	[Điền]	[Điền]	Hướng thử nghiệm backbone hiện đại

4.4.3. Lựa chọn mô hình cuối cùng
Mô hình VGG16 + Inception + Vision Transformer được chọn làm mô hình chính vì đạt kết quả tốt trên tập test và có kiến trúc phù hợp với đặc điểm ảnh tổn thương da. VGG16 học đặc trưng cục bộ, Inception bổ sung đặc trưng đa tỷ lệ, còn Vision Transformer học quan hệ giữa các vùng ảnh. So với mô hình CNN đơn giản, mô hình lai có khả năng biểu diễn tốt hơn. So với các backbone lớn hơn, mô hình này vẫn giữ được mức độ gọn nhẹ tương đối và dễ tích hợp vào pipeline thử nghiệm.
4.5. Đánh giá pipeline hoàn chỉnh
4.5.1. Một số ca phân tích ảnh minh họa
Pipeline hoàn chỉnh cần được minh họa bằng một số ảnh thực tế. Với mỗi ảnh, báo cáo nên trình bày ảnh đầu vào, bounding box YOLO, nhãn bệnh dự đoán, độ tin cậy và phản hồi RAG. Các ví dụ này giúp người đọc hiểu cách các mô hình phối hợp trong hệ thống.
Hình 4.5 Ví dụ pipeline phân tích ảnh thành công
Chèn ảnh giao diện có bounding box, tên bệnh, độ tin cậy và câu trả lời RAG.
4.5.2. Kết quả phản hồi RAG
RAG giúp hệ thống sinh phản hồi có ngữ cảnh thay vì chỉ trả về tên bệnh. Khi người dùng hỏi thêm về một kết quả phân tích, hệ thống truy xuất thông tin liên quan đến nhóm bệnh dự đoán rồi sinh câu trả lời bằng tiếng Việt. Phản hồi cần giữ tính thận trọng, tránh khẳng định chẩn đoán và luôn khuyến nghị xác nhận với bác sĩ da liễu.
4.5.3. Thời gian xử lý và trải nghiệm sử dụng
Thời gian xử lý của pipeline phụ thuộc vào detector, classifier và backend sinh văn bản. Phần phát hiện và phân loại ảnh thường nhanh hơn phần RAG nếu dùng mô hình ngôn ngữ chạy qua Ollama trên CPU. Nếu dùng OpenAI, phản hồi RAG có thể nhanh hơn nhưng phụ thuộc kết nối mạng và API key. Báo cáo có thể bổ sung thời gian xử lý trung bình nếu đã đo được.
Bảng 4.7 Thời gian xử lý pipeline cần bổ sung
Thành phần	Thời gian trung bình
Kiểm tra ảnh da	[Điền]
YOLO detection	[Điền]
Classification	[Điền]
RAG retrieval	[Điền]
LLM generation	[Điền]
Tổng thời gian	[Điền]

4.5.4. Hạn chế quan sát được
Pipeline vẫn còn một số hạn chế. Bộ phát hiện ảnh da dựa trên màu có thể bị ảnh hưởng bởi ánh sáng và nền ảnh. Detector YOLO phụ thuộc chất lượng bounding box được tạo từ mask. Classifier còn nhầm melanoma với nv và bkl, đây là điểm cần cải thiện. RAG phụ thuộc vào chất lượng cơ sở tri thức và khả năng truy xuất đúng đoạn liên quan. Vì vậy, kết quả của hệ thống chỉ nên được dùng làm thông tin tham khảo, không thay thế bác sĩ da liễu.
KẾT LUẬN

TÀI LIỆU THAM KHẢO
[1] Philipp Tschandl, Cliff Rosendahl, Harald Kittler, "The HAM10000 dataset, a large collection of multi-source dermatoscopic images of common pigmented skin lesions", Scientific Data, 2018. https://arxiv.org/abs/1803.10417
[2] Joseph Redmon, Santosh Divvala, Ross Girshick, Ali Farhadi, "You Only Look Once: Unified, Real-Time Object Detection", CVPR, 2016. https://arxiv.org/abs/1506.02640
[3] Rahima Khanam, Muhammad Hussain, "YOLOv11: An Overview of the Key Architectural Enhancements", arXiv, 2024. https://arxiv.org/abs/2410.17725
[4] Karen Simonyan, Andrew Zisserman, "Very Deep Convolutional Networks for Large-Scale Image Recognition", ICLR, 2015. https://arxiv.org/abs/1409.1556
[5] Alexey Dosovitskiy et al., "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale", ICLR, 2021. https://arxiv.org/abs/2010.11929
[6] Patrick Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", NeurIPS, 2020. https://arxiv.org/abs/2005.11401
[7] World Health Organization, "Ultraviolet radiation", Fact sheet, cập nhật ngày 25 tháng 7 năm 2022. https://www.who.int/news-room/fact-sheets/detail/ultraviolet-radiation
[8] American Cancer Society, "Survival Rates for Melanoma Skin Cancer", cập nhật theo dữ liệu SEER 2015-2021. https://www.cancer.org/cancer/types/melanoma-skin-cancer/detection-diagnosis-staging/survival-rates-for-melanoma-skin-cancer-by-stage.html
[9] Andre Esteva, Brett Kuprel, Roberto A. Novoa et al., "Dermatologist-level classification of skin cancer with deep neural networks", Nature, 2017. https://www.nature.com/articles/nature21056
[10] Poornima Singh Thakur, Pritee Khanna, Tanuja Sheorey, Aparajita Ojha, "Explainable vision transformer enabled convolutional neural network for plant disease identification: PlantXViT", arXiv, 2022. https://arxiv.org/abs/2207.07919
[11] Mst Shapna Akter, Hossain Shahriar, Sweta Sneha, Alfredo Cuzzocrea, "Multi-class Skin Cancer Classification Architecture Based on Deep Convolutional Neural Network", arXiv, 2023. https://arxiv.org/abs/2303.07520
[12] Ultralytics, "YOLOv8: A New State-of-the-Art Computer Vision Model", tài liệu mô hình YOLOv8. https://docs.ultralytics.com/models/yolov8/
[13] Ultralytics, "YOLO11 vs YOLOv8: A Comprehensive Technical Comparison of Real-Time Vision Models", tài liệu so sánh kỹ thuật. https://docs.ultralytics.com/compare/yolo11-vs-yolov8/
[14] Christian Szegedy, Wei Liu, Yangqing Jia et al., "Going Deeper with Convolutions", CVPR, 2015. https://arxiv.org/abs/1409.4842
[15] International Skin Imaging Collaboration, "ISIC 2018 Challenge - Task 1: Lesion Boundary Segmentation". https://challenge.isic-archive.com/landing/2018/45/
[16] Noel Codella, Veronica Rotemberg, Philipp Tschandl et al., "Skin Lesion Analysis Toward Melanoma Detection 2018: A Challenge Hosted by the International Skin Imaging Collaboration (ISIC)", arXiv, 2019. https://arxiv.org/abs/1902.03368
[17] Tsung-Yi Lin, Priya Goyal, Ross Girshick, Kaiming He, Piotr Dollár, "Focal Loss for Dense Object Detection", ICCV, 2017. https://arxiv.org/abs/1708.02002
[18] Yin Cui, Menglin Jia, Tsung-Yi Lin, Yang Song, Serge Belongie, "Class-Balanced Loss Based on Effective Number of Samples", CVPR, 2019. https://arxiv.org/abs/1901.05555
[19] Ilya Loshchilov, Frank Hutter, "Decoupled Weight Decay Regularization", ICLR, 2019. https://arxiv.org/abs/1711.05101
 
PHỤ LỤC A: GHI CHÚ CẦN BỔ SUNG CHO BẢN CHÍNH THỨC
Cần bổ sung thông tin sinh viên, giảng viên hướng dẫn, tên khoa, tên trường và năm thực hiện. Cần bổ sung số liệu huấn luyện và đánh giá thực tế từ notebook, bao gồm tập train, validation, test, số epoch, optimizer, learning rate, batch size, loss function, augmentation và cấu hình phần cứng. Cần chèn hình giao diện ứng dụng, hình pipeline, confusion matrix, biểu đồ loss/accuracy và ví dụ kết quả dự đoán đúng/sai.
Cần kiểm tra lại cấu hình pipeline mặc định trước khi bảo vệ. Nếu mô hình chính là VGG16 + Vision Transformer, nên đặt pipelines.default.classifier thành vgg_vit trong model_registry.json hoặc trong cấu hình active của database. Nếu vẫn giữ gpt_vision, báo cáo cần giải thích rõ đây là classifier tùy chọn và không phải kết quả chính của mô hình tự huấn luyện.
