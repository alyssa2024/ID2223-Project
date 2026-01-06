import os
import re
import html
import fitz  # PyMuPDF
import urllib.parse
from typing import List, Optional

class ContentProcessor:
    """
    负责读取本地文件(PDF/HTML)，进行清洗和分块。
    不包含任何 Hopsworks 或 Zotero 逻辑。
    """
    
    @staticmethod
    def read_file(file_path: str, mime_type: str) -> str:
        """入口函数：根据类型分发处理"""
        if not os.path.exists(file_path):
            # 尝试 URL 解码路径 (处理空格等)
            decoded_path = urllib.parse.unquote(file_path)
            if os.path.exists(decoded_path):
                file_path = decoded_path
            else:
                print(f"⚠️ File not found: {file_path}")
                return ""

        lower_path = file_path.lower()
        if "pdf" in mime_type or lower_path.endswith(".pdf"):
            return ContentProcessor._read_pdf(file_path)
        elif "html" in mime_type or lower_path.endswith(".html"):
            return ContentProcessor._read_html(file_path)
        return ""

    @staticmethod
    def _read_pdf(path: str) -> str:
        try:
            doc = fitz.open(path)
            # 优化：按 Block 读取可以更好处理双栏，这里简单按页读取后清洗
            text = "".join([page.get_text() for page in doc])
            doc.close()
            return ContentProcessor._clean_text(text)
        except Exception as e:
            print(f"❌ PDF Error ({os.path.basename(path)}): {e}")
            return ""

    @staticmethod
    def _read_html(path: str) -> str:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            # 去除脚本和样式
            content = re.sub(r'<(script|style).*?>.*?</\1>', '', content, flags=re.DOTALL)
            # 去除标签
            text = re.sub(r'<[^>]+>', ' ', content)
            text = html.unescape(text)
            return ContentProcessor._clean_text(text)
        except Exception as e:
            print(f"❌ HTML Error: {e}")
            return ""

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        [核心复用] 移植自 text_preprocess.py 的清洗逻辑
        """
        if not text: return ""
        
        # 1. 修复连字符断行 (trans-\nformer -> transformer)
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        
        # 2. 标准化换行 (Windows -> Unix)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # 3. 去除目录页常见的连续点/线 (复用你的正则)
        pattern_to_remove = r'(\.{5,}|\-{5,})'
        text = re.sub(pattern_to_remove, ' ', text)
        
        # 4. 去除多余空白 (保留段落结构是下一步的事，这里先清洗行内空白)
        # 注意：这里我们保留 \n 用于识别段落，只清洗 \t, \f, \u00A0
        text = re.sub(r"[\t\f\u00A0]+", " ", text)
        
        # 5. 压缩多余换行 (超过3个换行变成2个，保留段落感)
        text = re.sub(r"\n{3,}", "\n\n", text)
        
        return text.strip()

    @staticmethod
    def chunk_text(text: str, chunk_size=1000, overlap=100) -> List[str]:
        """
        智能分块：先尝试按段落切分，段落过长再强行切分。
        """
        if not text: return []
        
        # 利用 \n\n 识别自然段落 (复用 split_page 思路)
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para: continue
            
            # 如果加入当前段落不超限，则合并
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += "\n\n" + para if current_chunk else para
            else:
                # 当前块已满，保存
                if current_chunk: 
                    chunks.append(current_chunk)
                    # 简单实现滑动窗口：保留上一块的尾部作为 Context (Overlap)
                    current_chunk = current_chunk[-overlap:] + "\n\n" + para
                
                # 如果单个段落本身就巨长(超过 chunk_size)，则强制切分
                if len(current_chunk) > chunk_size:
                    # 强制切分 current_chunk
                    for i in range(0, len(current_chunk), chunk_size - overlap):
                        chunks.append(current_chunk[i:i+chunk_size])
                    current_chunk = "" # 清空

        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

    @staticmethod
    def extract_abstract_fallback(text: str) -> Optional[str]:
        """[复用] 当 Zotero 没有摘要时，尝试从全文提取"""
        # 这里可以直接粘贴你之前提供的 extract_abstract_from_text 函数代码
        # 为节省篇幅，此处省略，实际使用时请完整粘贴
        if len(text) > 1000: return text[:1000] # 简易版兜底
        return None
