"""
Giao diện web cho hệ thống chatbot triết học
Sử dụng Streamlit để tạo UI chat tương tác
"""

import streamlit as st
import logging
from typing import Dict, List
import json
from datetime import datetime
import time

from config import PHILOSOPHY_SCHOOLS
from socratic_wrapper import SocraticChatbot
from utils import create_sample_data
from pathlib import Path

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cấu hình Streamlit
st.set_page_config(
    page_title="🏛️ Chatbot Triết Học Socrates",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tùy chỉnh cho giao diện đẹp hơn
def load_css():
    """Tải CSS tùy chỉnh"""
    st.markdown("""
    <style>
    /* Tùy chỉnh sidebar */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f0f2f6 0%, #e8eaf0 100%);
    }
    
    /* Tùy chỉnh chat messages */
    .user-message {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    
    .assistant-message {
        background-color: #f3e5f5;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    
    .socratic-question {
        background-color: #fff3e0;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
        border-left: 4px solid #ff9800;
    }
    
    /* Tùy chỉnh sources */
    .source-box {
        background-color: #f5f5f5;
        padding: 8px;
        border-radius: 5px;
        margin-top: 5px;
        font-size: 0.9em;
    }
    
    /* School info box */
    .school-info {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def initialize_chatbot(school: str) -> SocraticChatbot:
    """
    Khởi tạo và cache chatbot
    
    Args:
        school: Tên trường phái
        
    Returns:
        Instance của SocraticChatbot
    """
    try:
        chatbot = SocraticChatbot(school, use_gpu=True)
        return chatbot
    except Exception as e:
        logger.error(f"Lỗi khởi tạo chatbot {school}: {e}")
        st.error(f"Không thể khởi tạo chatbot cho {school}. Vui lòng kiểm tra dữ liệu.")
        return None

def render_message(message: Dict, is_user: bool = False):
    """
    Render một message trong chat
    
    Args:
        message: Dictionary chứa nội dung message
        is_user: True nếu là message từ user
    """
    if is_user:
        with st.chat_message("user", avatar="🧑"):
            st.write(message["content"])
    else:
        with st.chat_message("assistant", avatar="🏛️"):
            st.write(message["content"])
            
            # Hiển thị sources nếu có
            if "sources" in message and message["sources"]:
                with st.expander("📚 Nguồn tham khảo", expanded=False):
                    for i, source in enumerate(message["sources"], 1):
                        st.caption(f"**Nguồn {i}** (Độ tin cậy: {source['score']:.2f})")
                        st.text(source['text'][:200] + "...")
            
            # Hiển thị độ tin cậy
            if "confidence" in message and message["confidence"] > 0:
                st.progress(message["confidence"], text=f"Độ tin cậy: {message['confidence']:.0%}")

def render_sidebar():
    """
    Render sidebar với các tùy chọn
    
    Returns:
        Tuple của (selected_school, use_socratic, clear_chat)
    """
    with st.sidebar:
        st.title("⚙️ Cài đặt Chatbot")
        
        # Chọn trường phái triết học
        st.subheader("🏛️ Chọn Trường Phái")
        school_names = {k: v["name"] for k, v in PHILOSOPHY_SCHOOLS.items()}
        selected_school = st.selectbox(
            "Trường phái triết học",
            options=list(school_names.keys()),
            format_func=lambda x: school_names[x],
            help="Chọn một trong 6 trường phái triết học để bắt đầu"
        )
        
        # Hiển thị thông tin trường phái
        if selected_school:
            school_info = PHILOSOPHY_SCHOOLS[selected_school]
            st.info(f"**{school_info['name']}**\n\n{school_info['description']}")
        
        st.divider()
        
        # Tùy chọn phương pháp
        st.subheader("💭 Phương pháp trả lời")
        use_socratic = st.toggle(
            "Sử dụng phương pháp Socrates",
            value=True,
            help="Chatbot sẽ đặt câu hỏi phản tư thay vì chỉ trả lời trực tiếp"
        )
        
        st.divider()
        
        # Nút xóa lịch sử
        st.subheader("🗑️ Quản lý hội thoại")
        clear_chat = st.button(
            "🔄 Bắt đầu hội thoại mới",
            use_container_width=True,
            type="secondary"
        )
        
        # Thống kê
        if 'chatbot' in st.session_state and st.session_state.chatbot:
            st.divider()
            st.subheader("📊 Thống kê")
            stats = st.session_state.chatbot.get_stats()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tổng câu hỏi", stats["total_questions"])
                st.metric("Tỷ lệ trả lời", f"{stats['answer_rate']:.0%}")
            with col2:
                st.metric("Câu hỏi Socrates", stats["socratic_responses"])
                st.metric("Tỷ lệ từ chối", f"{stats['rejection_rate']:.0%}")
        
        # Thông tin về dự án
        st.divider()
        st.caption("📖 Về dự án")
        st.caption(
            "Chatbot triết học sử dụng phương pháp Socrates. "
            "Dữ liệu được giới hạn trong phạm vi tài liệu đã cung cấp."
        )
        
    return selected_school, use_socratic, clear_chat

def main():
    """
    Hàm chính chạy ứng dụng Streamlit
    """
    # Load CSS
    load_css()
    
    # Header
    st.title("🏛️ Chatbot Triết Học Socrates")
    st.markdown(
        "**Khám phá triết học qua đối thoại** - "
        "Chatbot sử dụng phương pháp Socrates để dẫn dắt bạn tìm hiểu sâu hơn"
    )
    
    # Render sidebar và lấy settings
    selected_school, use_socratic, clear_chat = render_sidebar()
    
    # Kiểm tra và tạo dữ liệu mẫu nếu cần
    data_path = Path("data/raw") / selected_school
    if not data_path.exists():
        with st.spinner("Đang tạo dữ liệu mẫu..."):
            create_sample_data()
            st.rerun()
    
    # Khởi tạo session state
    if 'messages' not in st.session_state:
        st.session_state.messages = {}
    
    if 'current_school' not in st.session_state:
        st.session_state.current_school = selected_school
    
    # Kiểm tra nếu đổi trường phái
    if st.session_state.current_school != selected_school:
        st.session_state.current_school = selected_school
        st.session_state.chatbot = None
        if selected_school not in st.session_state.messages:
            st.session_state.messages[selected_school] = []
    
    # Khởi tạo messages cho trường phái nếu chưa có
    if selected_school not in st.session_state.messages:
        st.session_state.messages[selected_school] = []
    
    # Xử lý clear chat
    if clear_chat:
        st.session_state.messages[selected_school] = []
        if 'chatbot' in st.session_state and st.session_state.chatbot:
            st.session_state.chatbot.reset()
        st.rerun()
    
    # Khởi tạo chatbot nếu chưa có
    if 'chatbot' not in st.session_state or st.session_state.chatbot is None:
        with st.spinner(f"Đang khởi tạo chatbot {PHILOSOPHY_SCHOOLS[selected_school]['name']}..."):
            chatbot = initialize_chatbot(selected_school)
            if chatbot:
                st.session_state.chatbot = chatbot
            else:
                st.error("Không thể khởi tạo chatbot. Vui lòng kiểm tra dữ liệu.")
                return
    
    # Container cho messages
    messages_container = st.container()
    
    # Hiển thị lịch sử chat
    with messages_container:
        for msg in st.session_state.messages[selected_school]:
            render_message(msg, is_user=(msg["role"] == "user"))
    
    # Chat input
    if prompt := st.chat_input("Đặt câu hỏi về triết học..."):
        # Thêm message của user
        user_message = {
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.messages[selected_school].append(user_message)
        
        # Hiển thị message của user
        with messages_container:
            render_message(user_message, is_user=True)
        
        # Generate response
        with st.spinner("Đang suy nghĩ..."):
            try:
                # Gọi chatbot
                result = st.session_state.chatbot.chat(
                    prompt,
                    use_socratic=use_socratic,
                    return_sources=True
                )
                
                # Tạo message từ response
                assistant_message = {
                    "role": "assistant",
                    "content": result["response"],
                    "sources": result.get("sources", []),
                    "confidence": result.get("confidence", 0),
                    "type": result.get("type", "direct"),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Thêm vào lịch sử
                st.session_state.messages[selected_school].append(assistant_message)
                
                # Hiển thị response
                with messages_container:
                    render_message(assistant_message, is_user=False)
                
            except Exception as e:
                logger.error(f"Lỗi khi generate response: {e}")
                st.error(f"Đã xảy ra lỗi: {str(e)}")
    
    # Footer với hướng dẫn
    with st.expander("📋 Hướng dẫn sử dụng", expanded=False):
        st.markdown("""
        ### Cách sử dụng chatbot:
        
        1. **Chọn trường phái triết học** ở sidebar bên trái
        2. **Bật/tắt phương pháp Socrates** tùy theo nhu cầu
        3. **Nhập câu hỏi** vào ô chat bên dưới
        4. Chatbot sẽ trả lời dựa trên tài liệu của trường phái đã chọn
        
        ### Lưu ý:
        - Chatbot chỉ trả lời trong phạm vi kiến thức của trường phái
        - Phương pháp Socrates sẽ đặt câu hỏi phản tư thay vì chỉ đưa câu trả lời
        - Mỗi câu trả lời đều có nguồn tham khảo từ tài liệu
        
        ### Các trường phái:
        - **Stoicism**: Triết học về kiểm soát cảm xúc và chấp nhận số phận
        - **Nihilism**: Triết học phủ nhận ý nghĩa tuyệt đối
        - **Phenomenology**: Nghiên cứu về ý thức và trải nghiệm
        - **Voluntarism**: Triết học đặt ý chí làm nền tảng
        - **Marxism**: Triết học về đấu tranh giai cấp
        - **Existentialism**: Triết học về tự do và trách nhiệm cá nhân
        """)

if __name__ == "__main__":
    main()