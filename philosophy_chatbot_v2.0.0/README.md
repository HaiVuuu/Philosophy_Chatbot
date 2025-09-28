# 🏛️ Hệ Thống Chatbot Triết Học Socrates

Hệ thống chatbot AI với 6 trường phái triết học, sử dụng phương pháp Socrates để dẫn dắt người dùng qua các câu hỏi phản tư thay vì chỉ đưa ra câu trả lời trực tiếp.

## 📚 6 Trường Phái Triết Học

1. **Stoicism (Khắc kỷ)** - Triết học về kiểm soát cảm xúc và chấp nhận số phận
2. **Nihilism (Hư vô)** - Triết học phủ nhận ý nghĩa và giá trị tuyệt đối
3. **Phenomenology (Hiện tượng học)** - Nghiên cứu về ý thức và trải nghiệm trực tiếp
4. **Voluntarism (Duy ý chí)** - Triết học đặt ý chí làm nền tảng của thực tại
5. **Marxism (Chủ nghĩa Marx)** - Triết học về đấu tranh giai cấp và biến đổi xã hội
6. **Existentialism (Hiện sinh)** - Triết học về tự do, lựa chọn và trách nhiệm cá nhân

## 🚀 Cài Đặt

### 1. Clone dự án
```bash
git clone https://github.com/your-repo/philosophy-chatbot.git
cd philosophy-chatbot
```

### 2. Tạo môi trường ảo (khuyến nghị)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows
```

### 3. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 4. Chuẩn bị dữ liệu
- Đặt file dữ liệu (TXT/PDF/CSV) vào thư mục tương ứng:
  ```
  data/raw/stoicism/       # Dữ liệu Stoicism
  data/raw/nihilism/       # Dữ liệu Nihilism
  data/raw/phenomenology/ # Dữ liệu Phenomenology
  data/raw/voluntarism/   # Dữ liệu Voluntarism
  data/raw/marxism/       # Dữ liệu Marxism
  data/raw/existentialism/# Dữ liệu Existentialism
  ```
- Nếu chưa có dữ liệu, hệ thống sẽ tự động tạo dữ liệu mẫu

## 📦 Xử Lý Dữ Liệu

### Tạo Vector Database cho tất cả trường phái:
```bash
python data_preprocessing.py
```

Lệnh này sẽ:
- Đọc dữ liệu từ các file văn bản
- Làm sạch và tách thành chunks
- Tạo embeddings
- Lưu vào FAISS vector database

## 🎯 Chạy Ứng Dụng

### Khởi động giao diện web:
```bash
streamlit run app.py
```

Sau đó truy cập: http://localhost:8501

## 🧪 Đánh Giá Hệ Thống

### Đánh giá toàn bộ hệ thống:
```bash
python evaluation.py full
```

### Đánh giá một trường phái cụ thể:
```bash
python evaluation.py stoicism
python evaluation.py nihilism
# ...
```

## 📂 Cấu Trúc Dự Án

```
philosophy_chatbot/
├── data/
│   ├── raw/              # Dữ liệu thô cho mỗi trường phái
│   └── vector_db/        # FAISS databases đã xử lý
├── logs/                 # Log đánh giá
├── app.py                # Giao diện Streamlit
├── config.py             # Cấu hình hệ thống
├── data_preprocessing.py # Xử lý dữ liệu & tạo embeddings
├── rag_pipeline.py       # RAG retrieval & generation
├── socratic_wrapper.py   # Phương pháp Socrates
├── evaluation.py         # Đánh giá chất lượng
├── utils.py              # Hàm tiện ích
└── requirements.txt      # Thư viện cần thiết
```

## ⚙️ Cấu Hình

Chỉnh sửa file `config.py` để thay đổi:
- Model embedding: `EMBEDDING_MODEL`
- Model LLM: `LLM_MODEL`
- Kích thước chunk: `CHUNK_SIZE`
- Số lượng kết quả retrieval: `TOP_K_RETRIEVAL`
- Nhiệt độ generation: `TEMPERATURE`

## 💡 Tính Năng Chính

- **Phương pháp Socrates**: Chatbot đặt câu hỏi phản tư thay vì chỉ trả lời
- **RAG Pipeline**: Giới hạn tri thức trong phạm vi dữ liệu được cung cấp
- **Trích dẫn nguồn**: Mỗi câu trả lời đều có nguồn tham khảo
- **Từ chối lịch sự**: Từ chối trả lời khi câu hỏi ngoài phạm vi
- **Đánh giá tự động**: Hệ thống đánh giá chất lượng tích hợp sẵn

## 🔧 Tùy Chỉnh

### Thêm trường phái mới:
1. Thêm vào `PHILOSOPHY_SCHOOLS` trong `config.py`
2. Tạo thư mục dữ liệu trong `data/raw/`
3. Chạy `python data_preprocessing.py`

### Thay đổi model:
- Sử dụng model nhẹ hơn: Thay `LLM_MODEL` trong `config.py`
- Sử dụng GPU: Truyền `use_gpu=True` khi khởi tạo chatbot

## 🎓 Hướng Dẫn Sử Dụng

1. Chọn trường phái triết học ở sidebar
2. Nhập câu hỏi vào ô chat
3. Chatbot sẽ:
   - Tìm kiếm thông tin liên quan
   - Trả lời theo phương pháp Socrates
   - Hiển thị nguồn tham khảo
4. Bấm "Bắt đầu hội thoại mới" để reset

## 📊 Metrics Đánh Giá

- **Độ chính xác trong phạm vi**: Tỷ lệ trả lời đúng với câu hỏi liên quan
- **Độ chính xác từ chối**: Tỷ lệ từ chối đúng với câu hỏi ngoài phạm vi
- **Tỷ lệ trích dẫn nguồn**: Có bao nhiêu câu trả lời kèm nguồn
- **Tỷ lệ Socrates**: Tỷ lệ sử dụng phương pháp Socrates
- **Thời gian phản hồi**: Thời gian trung bình để trả lời

## ⚠️ Lưu Ý

- Lần chạy đầu tiên sẽ tải model (có thể mất vài phút)
- Dữ liệu mẫu chỉ để minh họa, cần thay bằng dữ liệu thật
- Nên sử dụng GPU để tăng tốc độ xử lý
- Vector database được cache, chỉ cần tạo 1 lần

## 🆘 Hỗ Trợ

Nếu gặp lỗi:
1. Kiểm tra đã cài đủ thư viện: `pip install -r requirements.txt`
2. Kiểm tra dữ liệu trong `data/raw/`
3. Xem log trong `logs/`
4. Chạy test: `python evaluation.py stoicism`

## 📝 License

MIT License - Tự do sử dụng cho mục đích giáo dục và nghiên cứu.