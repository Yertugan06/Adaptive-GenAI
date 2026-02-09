import re
from typing import List
from backend.schemas.nosql.document_chunk import DocumentChunk
from backend.services.bi_encoder import count_tokens, create_embedding
from unstructured.partition.docx import partition_docx

class DocumentProcessor:

    
    MAX_MODEL_TOKENS = 512
    CHUNK_SIZE_TOKENS = 400
    CHUNK_OVERLAP_TOKENS = 50
    
    @staticmethod
    def clean_text_for_embedding(text: str) -> str:
        cleaned = text
        cleaned = re.sub(r'"(\w+)":\s*"[^"]*"', r'\1 field', cleaned)
        cleaned = re.sub(r'"(\w+)":\s*[\d.]+', r'\1 value', cleaned)
        cleaned = re.sub(r'\^?\[?\^?@\]\+\$?', 'email pattern', cleaned)
        cleaned = re.sub(r'\\+', ' ', cleaned)
        cleaned = re.sub(r'[\^$\[\]{}()*+?|]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
    
    @classmethod
    def process_docx(cls, file_path: str, parent_id: str, company_id: int) -> List[DocumentChunk]:

        try:
            

            elements = partition_docx(file_path)
            

            sections = []
            current_section = []
            
            for element in elements:
                element_type = type(element).__name__
                text = str(element).strip()
                
                if not text:
                    continue
                

                if element_type in ['Title', 'Header']:
                    if current_section:
                        sections.append('\n'.join(current_section))
                        current_section = []
                    current_section.append(text)
                else:
                    current_section.append(text)
            

            if current_section:
                sections.append('\n'.join(current_section))
            

            full_text = '\n\n'.join(sections)
            

            return cls._create_chunks(full_text, parent_id, company_id)
            

        except Exception as e:
            print(f"Error processing DOCX {file_path}: {e}")
            raise
    
    @classmethod
    def _create_chunks(cls, text: str, parent_id: str, company_id: int) -> List[DocumentChunk]:

        chunks = []
        

        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        chunk_idx = 0
        
        for sentence in sentences:
            potential = f"{current_chunk} {sentence}".strip() if current_chunk else sentence
            
            if count_tokens(potential) > cls.CHUNK_SIZE_TOKENS:
                if current_chunk:

                    cleaned = cls.clean_text_for_embedding(current_chunk)
                    chunks.append(DocumentChunk(
                        parent_doc_id=parent_id,
                        company_id=company_id,
                        chunk_index=chunk_idx,
                        content=current_chunk,  
                        embedding=create_embedding(cleaned), 
                    ))
                    chunk_idx += 1
                current_chunk = sentence
            else:
                current_chunk = potential
        
        if current_chunk:
            cleaned = cls.clean_text_for_embedding(current_chunk)
            chunks.append(DocumentChunk(
                parent_doc_id=parent_id,
                company_id=company_id,
                chunk_index=chunk_idx,
                content=current_chunk,
                embedding=create_embedding(cleaned),
            ))
        
        return chunks


