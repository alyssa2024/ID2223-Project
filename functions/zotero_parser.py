import os
import re
from pathlib import Path
from rdflib import RDF, Graph, Namespace
from rdflib.namespace import DC, DCTERMS, FOAF

# 定义 RDF 命名空间
Z = Namespace("http://www.zotero.org/namespaces/export#")
BIB = Namespace("http://purl.org/net/biblio#")
LINK = Namespace("http://purl.org/rss/1.0/modules/link/")

class ZoteroRDFParser:
    """
    负责解析 Zotero RDF 文件，提取元数据和附件路径。
    """
    def __init__(self, rdf_file_path: str, base_attachment_dir: str = "."):
        self.rdf_file_path = Path(rdf_file_path)
        self.base_dir = base_attachment_dir
        self.graph = Graph()
        self.papers = []
        self.attachments_map = {} # {paper_id: [{"path": str, "type": str}]}
        self.collections_map = {} # {collection_id: "AI/LLM/RAG"}

    def parse(self):
        print(f"📖 Parsing RDF file: {self.rdf_file_path}...")
        try:
            self.graph.parse(str(self.rdf_file_path), format="xml")
        except Exception as e:
            print(f"❌ RDF Parse Error: {e}")
            return []

        # 1. 预处理目录结构 (Collections)
        self._parse_collections()

        # 2. 预处理附件关联 (Attachments)
        self._parse_attachments()
        
        # 3. 解析论文条目
        self._parse_papers()
        
        print(f"✅ Found {len(self.papers)} valid papers in Zotero library.")
        return self.papers

    def _parse_collections(self):
        """解析目录层级，暂略（如果需要复杂的目录映射可在此扩展）"""
        pass

    def _parse_attachments(self):
        """建立 Paper -> Attachments 的映射"""
        for attach_subj, _, _ in self.graph.triples((None, RDF.type, Z.Attachment)):
            # 获取文件路径
            file_path = None
            for _, _, res in self.graph.triples((attach_subj, RDF.resource, None)):
                file_path = str(res)
            
            # 获取文件类型 (MIME)
            mime_type = "application/pdf" # 默认为 PDF
            for _, _, mtype in self.graph.triples((attach_subj, LINK.type, None)):
                mime_type = str(mtype)

            if file_path:
                # 找到所属的论文
                for paper_subj, _, _ in self.graph.triples((None, LINK.link, attach_subj)):
                    paper_id = str(paper_subj)
                    if paper_id not in self.attachments_map:
                        self.attachments_map[paper_id] = []
                    
                    self.attachments_map[paper_id].append({
                        "path": file_path,
                        "type": mime_type
                    })

    def _parse_papers(self):
        target_types = [
            "conferencepaper", "journalarticle", "article", 
            "book", "booksection", "preprint", "webpage", "report"
        ]
        
        for subj, _, obj in self.graph.triples((None, Z.itemType, None)):
            if str(obj).lower() in target_types:
                paper = self._extract_paper_metadata(subj)
                if paper:
                    self.papers.append(paper)

    def _extract_paper_metadata(self, paper_subj):
        paper_id = str(paper_subj)
        
        # Title
        title = ""
        for _, _, t in self.graph.triples((paper_subj, DC.title, None)):
            title = str(t).strip()
        if not title: return None

        # Abstract
        abstract = ""
        for _, _, a in self.graph.triples((paper_subj, DCTERMS.abstract, None)):
            abstract = str(a).strip()

        # Year
        year = 2024
        for _, _, date_obj in self.graph.triples((paper_subj, DC.date, None)):
            match = re.search(r"(\d{4})", str(date_obj))
            if match: year = int(match.group(1))

        # Authors (拼接为字符串)
        authors_list = []
        for _, _, authors_seq in self.graph.triples((paper_subj, BIB.authors, None)):
            # 这里简化处理：尝试查找序列中的人名
            # 在实际 RDF 中，这通常是一个 rdf:Seq，这里做简化假设
            pass 
        authors_str = "Unknown" # 实际需要根据 RDF 结构完善作者解析

        # Category / Tags (从 Zotero 的 Subject 字段提取)
        subjects = []
        for _, _, subj in self.graph.triples((paper_subj, DC.subject, None)):
            subjects.append(str(subj))
        category = ", ".join(subjects) if subjects else "Uncategorized"

        # 关联附件
        attachments = self.attachments_map.get(paper_id, [])

        return {
            "id": paper_id.replace("urn:", "").replace(":", "_"),
            "title": title,
            "abstract": abstract,
            "year": year,
            "authors": authors_str,
            "category": category,
            "attachments": attachments
        }
