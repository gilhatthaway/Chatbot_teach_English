"""
Memory Management Module
Quản lý lịch sử hội thoại cho chatbot
"""

class ConversationMemory:
    """Lưu trữ và quản lý lịch sử hội thoại của mỗi user"""
    
    def __init__(self, max_history=10):
        """
        Args:
            max_history: Số lượng hội thoại tối đa cần nhớ
        """
        self.memory = {}  # {id_user: [{"role": "user/assistant", "content": "..."}]}
        self.max_history = max_history
    
    def add_message(self, id_user, role, content):
        """
        Thêm tin nhắn vào lịch sử
        
        Args:
            id_user: ID của user
            role: "user" hoặc "assistant"
            content: Nội dung tin nhắn
        """
        if id_user not in self.memory:
            self.memory[id_user] = []
        
        self.memory[id_user].append({
            "role": role,
            "content": content
        })
        
        # Giữ chỉ max_history tin nhắn gần nhất
        if len(self.memory[id_user]) > self.max_history:
            self.memory[id_user] = self.memory[id_user][-self.max_history:]
    
    def get_history(self, id_user):
        """
        Lấy lịch sử hội thoại của user
        
        Args:
            id_user: ID của user
        
        Returns:
            List các tin nhắn hoặc []
        """
        return self.memory.get(id_user, [])
    
    def get_context(self, id_user):
        """
        Lấy context dạng string để gắn vào prompt
        
        Args:
            id_user: ID của user
        
        Returns:
            String chứa lịch sử hội thoại
        """
        history = self.get_history(id_user)
        if not history:
            return "Đây là lần đầu tiên bạn chat với tôi."
        
        context = "Lịch sử hội thoại trước:\n"
        for msg in history:
            role = "Bạn" if msg["role"] == "user" else "Tôi"
            context += f"{role}: {msg['content']}\n"
        
        return context
    
    def clear_history(self, id_user):
        """
        Xóa lịch sử hội thoại của user
        
        Args:
            id_user: ID của user
        """
        if id_user in self.memory:
            del self.memory[id_user]
    
    def clear_all(self):
        """Xóa toàn bộ lịch sử"""
        self.memory.clear()
    
    def get_stats(self, id_user):
        """
        Lấy thống kê hội thoại
        
        Args:
            id_user: ID của user
        
        Returns:
            Dict chứa số tin nhắn của user/assistant
        """
        history = self.get_history(id_user)
        user_msgs = sum(1 for msg in history if msg["role"] == "user")
        assistant_msgs = sum(1 for msg in history if msg["role"] == "assistant")
        
        return {
            "total_messages": len(history),
            "user_messages": user_msgs,
            "assistant_messages": assistant_msgs
        }


# Khởi tạo global memory instance
conversation_memory = ConversationMemory(max_history=15)
