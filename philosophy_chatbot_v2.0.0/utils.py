"""
Các hàm tiện ích dùng chung trong hệ thống
"""

import os
import re
import logging
from typing import List, Dict, Any
import PyPDF2
import pandas as pd
from pathlib import Path

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_text_file(file_path: str) -> str:
    """
    Đọc file văn bản (TXT)
    
    Args:
        file_path: Đường dẫn tới file
        
    Returns:
        Nội dung văn bản
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Đã đọc file: {file_path}")
        return content
    except Exception as e:
        logger.error(f"Lỗi khi đọc file {file_path}: {e}")
        return ""

def read_pdf_file(file_path: str) -> str:
    """
    Đọc file PDF
    
    Args:
        file_path: Đường dẫn tới file PDF
        
    Returns:
        Nội dung văn bản từ PDF
    """
    try:
        content = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                content += page.extract_text() + "\n"
                
        logger.info(f"Đã đọc {num_pages} trang từ PDF: {file_path}")
        return content
    except Exception as e:
        logger.error(f"Lỗi khi đọc PDF {file_path}: {e}")
        return ""

def read_csv_file(file_path: str, text_column: str = 'text') -> str:
    """
    Đọc file CSV và trích xuất cột văn bản
    
    Args:
        file_path: Đường dẫn tới file CSV
        text_column: Tên cột chứa văn bản
        
    Returns:
        Nội dung văn bản từ CSV
    """
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        if text_column in df.columns:
            content = "\n".join(df[text_column].astype(str).tolist())
        else:
            # Nếu không có cột được chỉ định, gộp tất cả các cột
            content = "\n".join(df.astype(str).apply(' '.join, axis=1).tolist())
        
        logger.info(f"Đã đọc {len(df)} dòng từ CSV: {file_path}")
        return content
    except Exception as e:
        logger.error(f"Lỗi khi đọc CSV {file_path}: {e}")
        return ""

def clean_text(text: str) -> str:
    """
    Làm sạch văn bản
    
    Args:
        text: Văn bản cần làm sạch
        
    Returns:
        Văn bản đã được làm sạch
    """
    # Xóa các ký tự đặc biệt không cần thiết
    text = re.sub(r'\s+', ' ', text)  # Chuẩn hóa khoảng trắng
    text = re.sub(r'\n+', '\n', text)  # Chuẩn hóa xuống dòng
    text = re.sub(r'[^\w\s\-.,;:!?""''()]', '', text)  # Giữ lại ký tự cần thiết
    
    # Xóa khoảng trắng thừa ở đầu và cuối
    text = text.strip()
    
    return text

def split_into_chunks(text: str, chunk_size: int = 250, overlap: int = 50) -> List[str]:
    """
    Chia văn bản thành các đoạn nhỏ (chunks)
    
    Args:
        text: Văn bản cần chia
        chunk_size: Kích thước mỗi chunk (số từ)
        overlap: Số từ overlap giữa các chunk
        
    Returns:
        Danh sách các chunks
    """
    # Tách văn bản thành các câu
    sentences = re.split(r'[.!?]\s+', text)
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        words = sentence.split()
        sentence_size = len(words)
        
        if current_size + sentence_size <= chunk_size:
            current_chunk.append(sentence)
            current_size += sentence_size
        else:
            if current_chunk:
                chunk_text = '. '.join(current_chunk) + '.'
                chunks.append(chunk_text)
                
                # Giữ lại một phần cho overlap
                if overlap > 0:
                    overlap_sentences = []
                    overlap_size = 0
                    for s in reversed(current_chunk):
                        s_size = len(s.split())
                        if overlap_size + s_size <= overlap:
                            overlap_sentences.insert(0, s)
                            overlap_size += s_size
                        else:
                            break
                    current_chunk = overlap_sentences
                    current_size = overlap_size
                else:
                    current_chunk = []
                    current_size = 0
            
            current_chunk.append(sentence)
            current_size = sentence_size
    
    # Thêm chunk cuối cùng
    if current_chunk:
        chunk_text = '. '.join(current_chunk) + '.'
        chunks.append(chunk_text)
    
    logger.info(f"Đã chia văn bản thành {len(chunks)} chunks")
    return chunks

def load_data_from_directory(directory_path: str) -> str:
    """
    Đọc tất cả file trong thư mục và gộp nội dung
    
    Args:
        directory_path: Đường dẫn tới thư mục
        
    Returns:
        Nội dung văn bản gộp
    """
    all_content = []
    directory = Path(directory_path)
    
    if not directory.exists():
        logger.warning(f"Thư mục không tồn tại: {directory_path}")
        return ""
    
    # Đọc các loại file khác nhau
    for file_path in directory.iterdir():
        if file_path.suffix.lower() == '.txt':
            content = read_text_file(str(file_path))
        elif file_path.suffix.lower() == '.pdf':
            content = read_pdf_file(str(file_path))
        elif file_path.suffix.lower() == '.csv':
            content = read_csv_file(str(file_path))
        else:
            continue
            
        if content:
            all_content.append(content)
    
    combined_content = "\n\n".join(all_content)
    logger.info(f"Đã đọc {len(all_content)} file từ {directory_path}")
    
    return combined_content

def create_sample_data():
    """
    Tạo dữ liệu mẫu cho các trường phái triết học
    """
    from config import RAW_DATA_DIR, PHILOSOPHY_SCHOOLS
    
    sample_data = {
        "stoicism": """
        Triết học Khắc kỷ (Stoicism) là một trường phái triết học Hy Lạp cổ đại, được sáng lập bởi Zeno xứ Citium tại Athens vào đầu thế kỷ thứ 3 TCN. Triết lý này nhấn mạnh rằng đức hạnh (virtue) là điều tốt đẹp duy nhất và là chìa khóa để đạt được eudaimonia (hạnh phúc hoặc sự thịnh vượng). Người theo chủ nghĩa Khắc kỷ tin rằng sống một cuộc đời có đức hạnh là sống phù hợp với tự nhiên và lý trí (Logos).

        Nguyên tắc cốt lõi: Lưỡng phân về quyền kiểm soát
        Một trong những khái niệm nền tảng của Khắc kỷ là "lưỡng phân về quyền kiểm soát" (dichotomy of control), được Epictetus trình bày rõ ràng. Theo đó, mọi thứ trong cuộc sống được chia thành hai loại: những gì chúng ta có thể kiểm soát và những gì chúng ta không thể kiểm soát. Những gì ta kiểm soát được bao gồm suy nghĩ, nhận định, quyết định và hành động của chính mình. Những gì ta không kiểm soát được bao gồm cơ thể, tài sản, danh tiếng và các sự kiện bên ngoài. Hạnh phúc và sự bình yên nội tâm chỉ có thể đạt được khi chúng ta tập trung nỗ lực vào những gì mình có thể kiểm soát và chấp nhận một cách thanh thản những gì nằm ngoài tầm tay.

        Bốn đức hạnh chính
        Để sống một cuộc đời tốt đẹp, người Khắc kỷ rèn luyện bốn đức hạnh cốt lõi:
        1. Trí tuệ (Sophia): Khả năng phân biệt điều tốt, điều xấu và điều trung tính; hiểu biết về thế giới và vị trí của con người trong đó.
        2. Công lý (Dikaiosyne): Hành động công bằng và tử tế với người khác, đối xử với mọi người theo đúng giá trị của họ như những thành viên của cộng đồng nhân loại.
        3. Can đảm (Andreia): Sức mạnh tinh thần để đối mặt với khó khăn, sợ hãi và đau đớn; kiên trì làm điều đúng đắn bất chấp nghịch cảnh.
        4. Tiết chế (Sophrosyne): Sự điều độ, tự chủ và kỷ luật; khả năng kiểm soát ham muốn và cảm xúc để không bị chúng chi phối.

        Chấp nhận số phận và Amor Fati
        Người Khắc kỷ tin vào một vũ trụ được sắp đặt bởi một lý trí phổ quát (Logos). Do đó, mọi sự kiện xảy ra đều là một phần của một kế hoạch lớn hơn và không thể tránh khỏi. Thay vì chống lại số phận, họ thực hành "Amor Fati" (Tình yêu với số phận) - không chỉ chịu đựng mà còn yêu thương và chào đón mọi điều xảy ra, xem đó là cơ hội để rèn luyện đức hạnh. Marcus Aurelius, hoàng đế La Mã và triết gia Khắc kỷ, đã viết trong "Suy tưởng": "Chướng ngại vật trên đường đi trở thành con đường."

        Thực hành trong đời sống
        Khắc kỷ không chỉ là lý thuyết mà còn là một lối sống thực hành. Các bài tập tinh thần bao gồm:
        - Tưởng tượng tiêu cực (Premeditatio Malorum): Suy ngẫm về những điều tồi tệ có thể xảy ra để chuẩn bị tinh thần và trân trọng những gì mình đang có.
        - Viết nhật ký triết học: Tự vấn và ghi lại suy nghĩ hàng ngày để theo dõi sự tiến bộ trong việc rèn luyện đức hạnh.
        - Nhìn từ trên cao (View from above): Hình dung bản thân và các vấn đề của mình từ một góc nhìn vũ trụ để thấy được sự nhỏ bé và tầm thường của những lo lắng cá nhân.
        """,
        
        "nihilism": """
        Chủ nghĩa Hư vô (Nihilism) là quan điểm triết học cho rằng cuộc sống không có ý nghĩa, mục đích, hoặc giá trị nội tại. Nó phủ nhận sự tồn tại của các nền tảng khách quan cho đạo đức, tri thức và trật tự xã hội. Chủ nghĩa hư vô thường được hiểu một cách tiêu cực, gắn liền với sự tuyệt vọng và sự hủy diệt, nhưng nó cũng có thể được xem như một điểm khởi đầu cho sự tự do cá nhân.

        Nietzsche và "Cái chết của Thượng đế"
        Friedrich Nietzsche là triết gia gắn liền mật thiết với chủ nghĩa hư vô. Ông không phải là người cổ xúy cho nó, mà là người chẩn đoán nó như một căn bệnh của văn hóa phương Tây. Tuyên bố nổi tiếng của ông "Thượng đế đã chết" (God is dead) không phải là một lời reo mừng mà là một sự thừa nhận rằng nền tảng của các giá trị đạo đức Do Thái-Kitô giáo đã sụp đổ. Khi không còn Thượng đế để bảo chứng cho ý nghĩa và đạo đức, con người sẽ rơi vào một khoảng trống hư vô.

        Hư vô chủ động và thụ động
        Nietzsche phân biệt hai loại hư vô:
        1. Hư vô thụ động: Đây là sự mệt mỏi, buông xuôi và tuyệt vọng khi nhận ra các giá trị cũ đã mất hiệu lực. Người theo hư vô thụ động chỉ đơn giản là từ bỏ việc tìm kiếm ý nghĩa.
        2. Hư vô chủ động: Đây là một dấu hiệu của sức mạnh. Người theo hư vô chủ động nhận ra sự vô nghĩa của các giá trị cũ và chủ động phá hủy chúng để dọn đường cho việc sáng tạo ra các giá trị mới. Đây là bước đệm cần thiết để trở thành Übermensch (Siêu nhân) - một cá nhân tự tạo ra hệ giá trị cho riêng mình.

        Hư vô Hiện sinh
        Trong bối cảnh của chủ nghĩa hiện sinh, hư vô là sự thừa nhận rằng không có ý nghĩa hay mục đích nào được định sẵn cho con người. Tuy nhiên, thay vì chìm trong tuyệt vọng, các nhà hiện sinh như Jean-Paul Sartre và Albert Camus cho rằng chính sự thiếu vắng ý nghĩa này lại là điều kiện cho tự do. Con người có thể và phải tự tạo ra ý nghĩa cho cuộc đời mình thông qua các lựa chọn và hành động.

        Hậu quả của Hư vô
        Dostoevsky trong tiểu thuyết "Anh em nhà Karamazov" đã khám phá một cách sâu sắc hậu quả của hư vô đạo đức thông qua nhân vật Ivan Karamazov với câu nói: "Nếu Thượng đế không tồn tại, mọi thứ đều được phép." Điều này đặt ra câu hỏi về nền tảng của đạo đức: nếu không có một quy luật thiêng liêng, điều gì ngăn cản con người khỏi những hành vi tàn ác nhất? Chủ nghĩa hư vô thách thức chúng ta phải đối mặt với câu hỏi về cách xây dựng một hệ thống đạo đức và ý nghĩa mà không cần dựa vào các giá trị tuyệt đối.
        """,
        
        "phenomenology": """
        Hiện tượng học (Phenomenology) là một phương pháp và trường phái triết học được sáng lập bởi Edmund Husserl vào đầu thế kỷ 20. Mục tiêu chính của nó là nghiên cứu cấu trúc của trải nghiệm và ý thức từ góc nhìn của người thứ nhất. Khẩu hiệu của hiện tượng học là "Trở về với chính sự vật!" (Zu den Sachen selbst!), nghĩa là gạt bỏ các lý thuyết và giả định để mô tả một cách trung thực cách sự vật hiện ra trong ý thức của chúng ta.

        Phương pháp Epoché và Giảm trừ Hiện tượng học
        Để nghiên cứu ý thức một cách thuần túy, Husserl đã đề xuất phương pháp "epoché" (sự đình chỉ phán đoán). Điều này bao gồm việc "đặt trong ngoặc" hay tạm gác lại niềm tin của chúng ta về sự tồn tại của thế giới bên ngoài. Chúng ta không phủ nhận thế giới, mà chỉ tạm thời không quan tâm đến câu hỏi liệu nó có thật hay không. Bằng cách này, chúng ta có thể tập trung hoàn toàn vào các hành vi của ý thức (noesis) và nội dung của chúng (noema) khi chúng hiện ra.

        Ý hướng tính (Intentionality)
        Một khái niệm trung tâm của hiện tượng học là "ý hướng tính", do Franz Brentano phát triển và Husserl kế thừa. Nó khẳng định rằng ý thức luôn là ý thức "về" một cái gì đó. Mọi hành vi tinh thần như suy nghĩ, nhận thức, mong muốn, hay tưởng tượng đều luôn hướng đến một đối tượng. Ví dụ, bạn không thể chỉ "nhìn" một cách chung chung, bạn phải nhìn "một cái cây" hoặc "một cuốn sách". Ý hướng tính là đặc tính cốt lõi kết nối chủ thể và đối tượng trong trải nghiệm.

        Thế giới sống (Lebenswelt)
        Trong giai đoạn sau, Husserl phát triển khái niệm "Lebenswelt" (thế giới sống). Đây là thế giới của trải nghiệm trực tiếp, tiền khoa học, nơi chúng ta sống và hành động hàng ngày. Ông cho rằng khoa học hiện đại đã tạo ra một cái nhìn trừu tượng về thế giới, che lấp đi nền tảng kinh nghiệm phong phú của thế giới sống. Hiện tượng học có nhiệm vụ khám phá lại nền tảng này.

        Sự phát triển của Hiện tượng học
        Các học trò của Husserl đã phát triển hiện tượng học theo nhiều hướng khác nhau.
        - Martin Heidegger đã chuyển trọng tâm từ ý thức thuần túy sang phân tích "Dasein" (Tồn-tại-ở-đây, hiện hữu của con người), xem xét sự tồn tại của con người như là "Tồn-tại-trong-thế-giới".
        - Maurice Merleau-Ponty nhấn mạnh vai trò của thân thể trong tri giác, cho rằng thân thể không phải là một vật thể mà là phương tiện để chúng ta trải nghiệm và tương tác với thế giới.
        - Jean-Paul Sartre áp dụng hiện tượng học để phân tích cấu trúc của tự do và sự tự lừa dối (bad faith).
        """,

        "voluntarism": """
        Chủ nghĩa Duy ý chí (Voluntarism) là một trường phái triết học coi ý chí (will) là nguyên lý cơ bản và tối cao của thực tại. Nó đặt ý chí lên trên lý trí và trí tuệ, cho rằng ý chí là động lực chính đằng sau mọi hiện tượng, từ vũ trụ đến hành vi của con người. Hai đại diện tiêu biểu nhất của chủ nghĩa duy ý chí là Arthur Schopenhauer và Friedrich Nietzsche.

        Arthur Schopenhauer và Ý chí sống
        Schopenhauer, trong tác phẩm chính "Thế giới như là Ý chí và Biểu tượng", đã trình bày một vũ trụ quan bi quan, trong đó bản chất sâu xa nhất của mọi sự vật là một Ý chí (Will) mù quáng, vô lý và không ngừng khao khát. Ý chí này là một xung lực nguyên thủy, hiện diện trong mọi thứ, từ lực hấp dẫn của các hành tinh đến ham muốn sống của sinh vật.
        Theo Schopenhauer, vì Ý chí là một sự khao khát không bao giờ được thỏa mãn hoàn toàn, nên cuộc sống về cơ bản là đau khổ. Hạnh phúc chỉ là sự tạm thời chấm dứt một nỗi đau, để rồi một ham muốn mới lại nảy sinh. Con người là nô lệ của "Ý chí-muốn-sống" (Wille zum Leben), một sự thôi thúc mù quáng để tồn tại và sinh sản.

        Lối thoát khỏi đau khổ
        Schopenhauer đề xuất hai con đường để tạm thời thoát khỏi sự kìm kẹp của Ý chí:
        1. Trải nghiệm thẩm mỹ: Khi chiêm ngưỡng nghệ thuật, chúng ta tạm thời trở thành một "chủ thể nhận thức thuần túy", không còn bị chi phối bởi các ham muốn cá nhân. Trong khoảnh khắc đó, chúng ta thoát khỏi vòng quay đau khổ.
        2. Lòng trắc ẩn và khổ hạnh: Bằng cách nhận ra rằng tất cả chúng ta đều là biểu hiện của cùng một Ý chí đau khổ, chúng ta phát triển lòng trắc ẩn. Lối sống khổ hạnh, từ bỏ mọi ham muốn, là con đường tối cao để phủ nhận Ý chí và đạt được sự bình yên.

        Friedrich Nietzsche và Ý chí quyền lực
        Nietzsche đã tiếp thu và biến đổi khái niệm Ý chí của Schopenhauer. Thay vì một Ý chí-muốn-sống tiêu cực, Nietzsche đề xuất "Ý chí quyền lực" (Der Wille zur Macht). Đây không chỉ đơn thuần là ham muốn tồn tại, mà là một động lực nội tại để phát triển, vượt qua, mở rộng và khẳng định sức mạnh.
        Đối với Nietzsche, Ý chí quyền lực là động lực cơ bản của mọi sinh vật. Nó không nhất thiết có nghĩa là thống trị người khác, mà còn là sự tự vượt lên chính mình (self-overcoming), sự sáng tạo và sự áp đặt ý chí của mình lên thế giới để tạo ra ý nghĩa và giá trị. Ý chí quyền lực là một lực lượng sáng tạo, là câu trả lời cho sự trống rỗng của chủ nghĩa hư vô.
        """,
        
        "marxism": """
        Chủ nghĩa Marx (Marxism) là một hệ thống lý luận triết học, kinh tế và chính trị được phát triển bởi Karl Marx và Friedrich Engels. Cốt lõi của chủ nghĩa Marx là phương pháp phân tích dựa trên chủ nghĩa duy vật lịch sử, tập trung vào đấu tranh giai cấp và phê phán chủ nghĩa tư bản.

        Chủ nghĩa duy vật lịch sử
        Marx cho rằng không phải ý thức quyết định đời sống vật chất, mà ngược lại, đời sống vật chất quyết định ý thức. Lịch sử nhân loại được thúc đẩy bởi sự phát triển của "lực lượng sản xuất" (công nghệ, công cụ, lao động) và "quan hệ sản xuất" (quan hệ xã hội giữa người với người trong sản xuất, ví dụ như chủ nô-nô lệ, địa chủ-nông nô, tư sản-vô sản).
        Cơ sở hạ tầng (kinh tế) quyết định thượng tầng kiến trúc (chính trị, pháp luật, văn hóa, tôn giáo). Lịch sử tiến triển qua các cuộc đấu tranh giai cấp, khi mâu thuẫn giữa lực lượng sản xuất phát triển và quan hệ sản xuất lỗi thời trở nên gay gắt, dẫn đến một cuộc cách mạng xã hội.

        Phê phán chủ nghĩa tư bản và sự tha hóa
        Marx phân tích sâu sắc chủ nghĩa tư bản và chỉ ra những mâu thuẫn nội tại của nó. Một trong những khái niệm quan trọng là sự "tha hóa" (Entfremdung). Trong chủ nghĩa tư bản, người lao động bị tha hóa theo bốn cách:
        1. Tha hóa khỏi sản phẩm lao động: Sản phẩm họ làm ra không thuộc về họ mà thuộc về nhà tư bản.
        2. Tha hóa khỏi quá trình lao động: Lao động trở thành một hoạt động cưỡng bức, không mang tính sáng tạo, chỉ để kiếm sống.
        3. Tha hóa khỏi bản chất con người (Gattungswesen): Con người mất đi khả năng lao động tự do và sáng tạo, vốn là bản chất của loài người.
        4. Tha hóa khỏi đồng loại: Mối quan hệ giữa người với người bị biến thành quan hệ hàng hóa, cạnh tranh.

        Lý thuyết giá trị thặng dư
        Marx giải thích nguồn gốc của lợi nhuận tư bản thông qua lý thuyết "giá trị thặng dư". Giá trị của một hàng hóa được quyết định bởi lượng lao động xã hội cần thiết để sản xuất ra nó. Nhà tư bản trả cho công nhân tiền lương chỉ tương đương với giá trị sức lao động của họ (đủ để họ sống và tái sản xuất), nhưng trong ngày làm việc, công nhân tạo ra một lượng giá trị lớn hơn nhiều. Phần giá trị dôi ra đó chính là giá trị thặng dư, nguồn gốc của lợi nhuận mà nhà tư bản chiếm đoạt. Đây được xem là bản chất của sự bóc lột tư bản chủ nghĩa.

        Đấu tranh giai cấp và Cách mạng
        Lịch sử, theo Marx, là lịch sử của đấu tranh giai cấp. Trong chủ nghĩa tư bản, xã hội phân chia thành hai giai cấp chính đối kháng: giai cấp tư sản (sở hữu tư liệu sản xuất) và giai cấp vô sản (phải bán sức lao động để sống). Marx dự đoán rằng mâu thuẫn giữa hai giai cấp này sẽ ngày càng trở nên gay gắt, dẫn đến một cuộc cách mạng của giai cấp vô sản. Mục tiêu cuối cùng là thiết lập một xã hội cộng sản, không có giai cấp, không có sở hữu tư nhân về tư liệu sản xuất và không có nhà nước.
        """,
        
        "existentialism": """
        Chủ nghĩa Hiện sinh (Existentialism) là một trào lưu triết học tập trung vào sự tồn tại của cá nhân, tự do và trách nhiệm. Khẩu hiệu trung tâm của nó, do Jean-Paul Sartre đưa ra, là "Tồn tại có trước bản chất" (existence precedes essence). Điều này có nghĩa là con người không được sinh ra với một bản chất hay mục đích định sẵn. Thay vào đó, chúng ta được "ném" vào thế giới, tồn tại trước, và sau đó tự định hình bản chất của mình thông qua các lựa chọn và hành động.

        Tự do và Trách nhiệm
        Tự do là khái niệm cốt lõi của chủ nghĩa hiện sinh. Con người hoàn toàn tự do để lựa chọn con người mà mình muốn trở thành. Tuy nhiên, tự do này không phải là một món quà dễ chịu. Sartre gọi đó là một sự "kết án phải tự do" (condemned to be free). Bởi vì chúng ta tự do, chúng ta phải chịu trách nhiệm hoàn toàn cho mọi lựa chọn của mình, không chỉ cho bản thân mà còn cho toàn thể nhân loại. Mỗi hành động của chúng ta là một tuyên bố về việc con người nên như thế nào. Gánh nặng trách nhiệm này gây ra một cảm giác lo âu (Angst).

        Sự phi lý (The Absurd)
        Albert Camus, một nhà hiện sinh khác, tập trung vào khái niệm "phi lý". Sự phi lý nảy sinh từ sự đối đầu giữa khao khát tìm kiếm ý nghĩa và trật tự của con người với một vũ trụ im lặng, thờ ơ và vô nghĩa. Con người khao khát một lời giải thích, nhưng vũ trụ không đưa ra câu trả lời nào.
        Camus cho rằng có ba cách đối phó với sự phi lý: tự sát (trốn chạy), hy vọng siêu việt (tin vào một thế giới khác, một sự "tự sát triết học"), hoặc nổi loạn. Camus ủng hộ sự nổi loạn: chúng ta phải sống đối mặt với sự phi lý, thừa nhận nó mà không cần hy vọng, và tìm thấy giá trị trong chính cuộc đấu tranh đó. Hình ảnh Sisyphus bị kết án đẩy tảng đá lên núi mãi mãi, nhưng vẫn hạnh phúc trong cuộc đấu tranh của mình, là biểu tượng của người hùng phi lý.

        Sự tự lừa dối (Bad Faith)
        Sartre đưa ra khái niệm "mauvaise foi" (bad faith) để mô tả hành vi tự lừa dối khi chúng ta trốn tránh tự do của mình. Chúng ta rơi vào "bad faith" khi giả vờ rằng mình không có lựa chọn, đổ lỗi cho hoàn cảnh, bản chất, hoặc xã hội. Ví dụ, một người bồi bàn hành động như thể anh ta "chỉ là một người bồi bàn" và không thể làm khác, đang tự lừa dối mình. Sống một cách chân thực (authenticity) là thừa nhận và đón nhận tự do tuyệt đối của mình, dù nó có đáng sợ đến đâu.

        Chủ nghĩa hiện sinh nữ quyền
        Simone de Beauvoir, trong tác phẩm "Giới tính thứ hai", đã áp dụng các nguyên tắc hiện sinh vào phân tích vị thế của phụ nữ. Câu nói nổi tiếng của bà "Người ta không sinh ra là phụ nữ, mà trở thành phụ nữ" (One is not born, but rather becomes, a woman) cho thấy "tính nữ" không phải là một bản chất sinh học cố định mà là một cấu trúc xã hội được áp đặt lên phụ nữ. Bà kêu gọi phụ nữ hãy sử dụng tự do hiện sinh của mình để vượt qua các định kiến xã hội và tự định nghĩa bản thân.
        """
    }
    
    # Tạo thư mục và file cho mỗi trường phái
    for school_key in PHILOSOPHY_SCHOOLS.keys():
        school_dir = RAW_DATA_DIR / school_key
        school_dir.mkdir(parents=True, exist_ok=True)
        
        sample_file = school_dir / "sample.txt"
        with open(sample_file, 'w', encoding='utf-8') as f:
            f.write(sample_data.get(school_key, ""))
        
        logger.info(f"Đã tạo dữ liệu mẫu cho {school_key}: {sample_file}")

if __name__ == "__main__":
    # Test các hàm tiện ích
    create_sample_data()
    print("Đã tạo dữ liệu mẫu thành công!")