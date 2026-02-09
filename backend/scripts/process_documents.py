import asyncio
from pathlib import Path
from bson import ObjectId
from typing import Dict, List

# Import your existing components
from backend.services.document_processor import DocumentProcessor
from backend.schemas.nosql.document_chunk import DocumentChunk
from backend.core.database import mongo_db

# Use your existing collection
document_chunks_col = mongo_db.document_chunks

async def process_and_store_documents() -> Dict:
    """
    Process all 6 documents and store chunks directly to MongoDB.
    """
    raw_docs_path = Path("backend/storage/raw_docs")
    
    # Document mapping
    documents_info = [
        {
            "name": "AIML Project Implementation Handbook",
            "company_id": 1,
        },
        {
            "name": "Internal Machine Learning Platform User Manual", 
            "company_id": 1,
        },
        {
            "name": "Data Science Team Playbook",
            "company_id": 1,
        },
        {
            "name": "Data Governance Policy Framework",
            "company_id": 2,
        },
        {
            "name": "Data Engineering Standards",
            "company_id": 2,
        },
        {
            "name": "Enterprise Data Platform Implementation",
            "company_id": 2,
        }
    ]
    
    processor = DocumentProcessor()
    statistics = {
        "total_documents": 0,
        "total_chunks": 0,
        "company_1_chunks": 0,
        "company_2_chunks": 0,
        "errors": []
    }
    
    print("="*70)
    print("DOCUMENT PROCESSING AND STORAGE TO MONGODB")
    print("="*70)
    print(f"Collection: {document_chunks_col.name}")
    print("-"*70)
    
    for doc_info in documents_info:
        try:
            # Generate a unique parent ID for this document
            parent_id = ObjectId()
            
            # Find the actual file
            file_name = f"{doc_info['name']}.docx"
            file_path = raw_docs_path / file_name
            
            if not file_path.exists():
                error_msg = f"File not found: {file_path}"
                print(f"❌ {error_msg}")
                statistics["errors"].append(error_msg)
                continue
            
            print(f"\n📄 Processing: {doc_info['name']}")
            print(f"   Company ID: {doc_info['company_id']}")
            print(f"   Parent ID: {parent_id}")
            
            # Process the document - parent_doc_id must be string for your schema
            chunks: List[DocumentChunk] = processor.process_docx(
                file_path=str(file_path),
                parent_id=str(parent_id),  # Convert to string for PyObjectId
                company_id=doc_info['company_id']
            )
            
            if not chunks:
                error_msg = f"No chunks generated for {doc_info['name']}"
                print(f"⚠️  {error_msg}")
                statistics["errors"].append(error_msg)
                continue
            
            print(f"   Generated {len(chunks)} chunks")
            
            # Insert chunks into MongoDB (ASYNC)
            if chunks:
                # Prepare chunks for insertion
                chunks_to_insert = []
                for chunk in chunks:
                    # Use model_dump with by_alias=True to convert to dict with MongoDB field names
                    chunk_dict = chunk.model_dump(by_alias=True, exclude_none=True)
                    
                    # Remove _id if it's None (let MongoDB generate it)
                    if "_id" in chunk_dict and chunk_dict["_id"] is None:
                        del chunk_dict["_id"]
                    
                    chunks_to_insert.append(chunk_dict)
                
                # Insert into MongoDB (AWAIT the async operation)
                result = await document_chunks_col.insert_many(chunks_to_insert)
                inserted_count = len(result.inserted_ids)
                
                # Update statistics
                statistics["total_documents"] += 1
                statistics["total_chunks"] += inserted_count
                
                if doc_info['company_id'] == 1:
                    statistics["company_1_chunks"] += inserted_count
                else:
                    statistics["company_2_chunks"] += inserted_count
                
                print(f"   ✅ Stored {inserted_count} chunks")
                
                # Show sample info
                if chunks:
                    sample = chunks[0]
                    print(f"   Sample parent_doc_id: {sample.parent_doc_id}")
                    print(f"   Sample chunk_index: {sample.chunk_index}")
                    print(f"   Sample embedding length: {len(sample.embedding)}")
            
        except Exception as e:
            error_msg = f"Error processing {doc_info['name']}: {str(e)}"
            print(f"❌ {error_msg}")
            statistics["errors"].append(error_msg)
            import traceback
            traceback.print_exc()
    
    return statistics

async def verify_chunks_structure():
    """Verify that chunks follow the exact schema structure."""
    print("\n" + "="*70)
    print("VERIFYING CHUNK STRUCTURE")
    print("="*70)
    
    # Get one sample chunk (AWAIT the async operation)
    sample_chunk = await document_chunks_col.find_one()
    
    if sample_chunk:
        print("Sample chunk from MongoDB:")
        print(f"  _id: {sample_chunk.get('_id')} (type: {type(sample_chunk.get('_id'))})")
        print(f"  parent_doc_id: {sample_chunk.get('parent_doc_id')} (type: {type(sample_chunk.get('parent_doc_id'))})")
        print(f"  company_id: {sample_chunk.get('company_id')} (type: {type(sample_chunk.get('company_id'))})")
        print(f"  chunk_index: {sample_chunk.get('chunk_index')} (type: {type(sample_chunk.get('chunk_index'))})")
        print(f"  content length: {len(sample_chunk.get('content', ''))} chars")
        print(f"  embedding length: {len(sample_chunk.get('embedding', []))}")
        print(f"  page_number: {sample_chunk.get('page_number')}")
        print(f"  created_at: {sample_chunk.get('created_at')}")
        print(f"  schema_version: {sample_chunk.get('schema_version')}")
        
        # Verify types match schema
        print("\nSchema validation:")
        assert isinstance(sample_chunk.get('parent_doc_id'), str), "parent_doc_id should be string"
        assert isinstance(sample_chunk.get('company_id'), int), "company_id should be int"
        assert isinstance(sample_chunk.get('chunk_index'), int), "chunk_index should be int"
        assert isinstance(sample_chunk.get('content'), str), "content should be string"
        assert isinstance(sample_chunk.get('embedding'), list), "embedding should be list"
        print("✓ All types match schema")
    else:
        print("No chunks found in collection")

async def main():
    """Main async function."""
    print("\n🚀 Starting document processing...")
    
    # Check if raw_docs directory exists
    raw_docs_path = Path("backend/storage/raw_docs")
    if not raw_docs_path.exists():
        print(f"❌ Directory not found: {raw_docs_path}")
        return
    
    # List available files
    docx_files = list(raw_docs_path.glob("*.docx"))
    if not docx_files:
        print(f"❌ No .docx files found in {raw_docs_path}")
        return
    
    print(f"📁 Found {len(docx_files)} .docx files:")
    for file in docx_files:
        print(f"   - {file.name}")
    
    # Optional: Clear existing chunks
    existing_count = await document_chunks_col.count_documents({})
    if existing_count > 0:
        print(f"\n⚠️  Collection has {existing_count} existing chunks")
        response = input("Clear existing chunks? (yes/no): ")
        if response.lower() == 'yes':
            result = await document_chunks_col.delete_many({})
            print(f"✓ Cleared {result.deleted_count} chunks")
    
    # Process documents
    stats = await process_and_store_documents()
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Documents processed: {stats['total_documents']}")
    print(f"Total chunks stored: {stats['total_chunks']}")
    print(f"  - Company 1: {stats['company_1_chunks']} chunks")
    print(f"  - Company 2: {stats['company_2_chunks']} chunks")
    
    if stats['errors']:
        print(f"\nErrors: {len(stats['errors'])}")
        for error in stats['errors']:
            print(f"  - {error}")
    
    # Verify structure
    await verify_chunks_structure()
    
    # Final count
    final_count = await document_chunks_col.count_documents({})
    print(f"\n✅ All done!")
    print(f"📊 Total chunks in collection: {final_count}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())