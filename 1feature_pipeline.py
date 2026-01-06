import os
import pandas as pd
import hopsworks
from sentence_transformers import SentenceTransformer
from hsfs.embedding import EmbeddingIndex

# 引入模块
from zotero_parser import ZoteroRDFParser
from pdf_extractor import ContentProcessor

# --- 配置 ---
PROJECT_NAME = "你的Hopsworks项目名"
RDF_PATH = "My Library.rdf"
BASE_DIR = "."  # 附件文件夹根目录
MODEL_NAME = "all-MiniLM-L6-v2"

def main():
    # 1. 初始化解析器
    parser = ZoteroRDFParser(RDF_PATH, BASE_DIR)
    papers = parser.parse()
    
    if not papers:
        print("No papers found to process.")
        return

    # 准备两个数据列表 (双索引策略)
    metadata_rows = []   # 用于宽泛搜索 (Title, Abstract)
    fulltext_rows = []   # 用于深度阅读 (Full Text Chunks)

    print("🚀 Starting content extraction...")
    
    for paper in papers:
        # --- A. 处理正文 (提取全文) ---
        full_text = ""
        # 遍历该论文的所有附件，找到第一个能读出来的
        for attach in paper["attachments"]:
            full_path = os.path.join(BASE_DIR, attach["path"])
            content = ContentProcessor.read_file(full_path, attach["type"])
            if len(content) > 100: # 只有内容足够才算成功
                full_text = content
                break # 只要一份正文
        
        # 如果 Zotero 没摘要，尝试从全文补全
        if not paper["abstract"] and full_text:
            fallback_abs = ContentProcessor.extract_abstract_fallback(full_text)
            if fallback_abs:
                paper["abstract"] = fallback_abs
                print(f"✨ Extracted abstract for {paper['title'][:30]}...")

        # --- B. 构建 Metadata Row (Meta Index) ---
        # 即使没有正文，元数据也是有用的
        metadata_rows.append({
            "paper_id": paper["id"],
            "title": paper["title"],
            "abstract": paper["abstract"],
            "authors": paper["authors"],
            "year": paper["year"],
            "category": paper["category"],
            # 这是用于 Embedding 的文本：包含标题、摘要和分类
            "combined_text": f"Title: {paper['title']}\nCategory: {paper['category']}\nAbstract: {paper['abstract']}"
        })

        # --- C. 构建 Fulltext Rows (Content Index) ---
        if full_text:
            chunks = ContentProcessor.chunk_text(full_text)
            for i, chunk in enumerate(chunks):
                fulltext_rows.append({
                    "paper_id": paper["id"],
                    "chunk_index": i,
                    "content": chunk,
                    "year": paper["year"] # 保留年份用于过滤
                })

    # 2. 连接 Hopsworks
    print(f"💾 Connecting to Hopsworks Project: {PROJECT_NAME}...")
    project = hopsworks.login(project=PROJECT_NAME)
    fs = project.get_feature_store()
    
    # 加载 Embedding 模型
    model = SentenceTransformer(MODEL_NAME)

    # --- 3. 上传 Metadata Feature Group ---
    if metadata_rows:
        print(f"Processing {len(metadata_rows)} metadata records...")
        df_meta = pd.DataFrame(metadata_rows)
        # 生成向量
        df_meta['embedding'] = df_meta['combined_text'].apply(lambda x: model.encode(x).tolist())
        
        meta_fg = fs.get_or_create_feature_group(
            name="zotero_meta_fg",
            version=1,
            description="Paper Metadata (Abstracts) for Broad Search",
            primary_key=["paper_id"],
            online_enabled=True,
            embedding_index=EmbeddingIndex()
        )
        meta_fg.insert(df_meta)
        print("✅ Metadata Feature Group uploaded.")

    # --- 4. 上传 Full-Text Feature Group ---
    if fulltext_rows:
        print(f"Processing {len(fulltext_rows)} full-text chunks...")
        df_text = pd.DataFrame(fulltext_rows)
        # 生成向量
        df_text['embedding'] = df_text['content'].apply(lambda x: model.encode(x).tolist())
        
        text_fg = fs.get_or_create_feature_group(
            name="zotero_fulltext_fg",
            version=1,
            description="Full Text Chunks for Deep Reading",
            primary_key=["paper_id", "chunk_index"],
            online_enabled=True,
            embedding_index=EmbeddingIndex()
        )
        text_fg.insert(df_text)
        print("✅ Full-Text Feature Group uploaded.")

if __name__ == "__main__":
    main()
