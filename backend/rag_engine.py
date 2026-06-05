import os
from openai import OpenAI
from qdrant_client import QdrantClient
from backend import config

class RAGEngine:
    def __init__(self):
        # Initialize clients
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Local Qdrant client path
        self.qdrant_client = QdrantClient(path=config.QDRANT_PATH)
        self.collection_name = config.COLLECTION_NAME

    def get_embedding(self, text: str) -> list[float]:
        """Generate embedding using OpenAI API."""
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=config.EMBEDDING_MODEL
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            raise

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search local Qdrant database for similar chunks."""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                print(f"Collection '{self.collection_name}' not found. Returning empty list.")
                return []

            query_vector = self.get_embedding(query)
            search_results = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                with_payload=True
            )
            
            formatted_results = []
            for hit in search_results.points:
                payload = hit.payload
                formatted_results.append({
                    "doc_id": payload.get("doc_id"),
                    "title": payload.get("title"),
                    "category": payload.get("category"),
                    "section": payload.get("section"),
                    "source_file": payload.get("source_file"),
                    "page": payload.get("page", 1),
                    "content": payload.get("content"),
                    "score": hit.score
                })
            return formatted_results
        except Exception as e:
            print(f"Error searching Qdrant: {e}")
            return []

    def generate_answer(self, query: str, chunks: list[dict]) -> str:
        """Generate RAG response with citations using OpenAI GPT-4o."""
        if not chunks:
            return (
                "Üzgünüm, sorunuzla ilgili İnsan Kaynakları prosedürlerinde, "
                "politikalarında veya iş tanımlarında herhangi bir bilgi bulunamadı. "
                "Lütfen sorunuzu farklı kelimelerle deneyin veya İK departmanı ile iletişime geçin."
            )

        # Build context string with numbered sources
        context_parts = []
        for idx, chunk in enumerate(chunks):
            source_info = f"[{idx+1}] Kaynak: {chunk['title']}, Bölüm: {chunk['section']}, Dosya: {chunk['source_file']}, Sayfa: {chunk['page']}"
            context_parts.append(f"{source_info}\nİçerik: {chunk['content']}\n")
            
        context_str = "\n---\n".join(context_parts)

        # Build prompt
        system_prompt = (
            "Sen bir kurumsal İnsan Kaynakları Yapay Zeka Asistanısın (HR Copilot AI).\n"
            "Görevin, kullanıcıların (çalışanlar, yöneticiler, İK uzmanları) sorularına "
            "SADECE ve SADECE sana sağlanan döküman parçalarını (context) kullanarak DOĞRU ve NET cevaplar vermektir.\n\n"
            "Kurallar:\n"
            "1. Sadece verilen döküman içeriğini referans al. Dışarıdan bilgi ekleme, uydurma.\n"
            "2. Cevap verirken kullandığın bilgilerin hangi dökümana ait olduğunu kaynak numarasıyla belirt. "
            "Örneğin: 'Çalışan El Kitabına göre, yıllık izin hakkı 14 gündür [1].' veya 'İş Kanunu madde 53'e göre izin süreleri belirlenir [2][3].'\n"
            "3. Cevabın sonunda kullanılan kaynakları detaylı liste halinde göster. Örnek:\n"
            "   **Kaynaklar:**\n"
            "   - [1] Çalışan El Kitabı, Sayfa 12 (Dosya: calisan_el_kitabi.pdf)\n"
            "   - [2] 4857 Sayılı İş Kanunu, Sayfa 2 (Dosya: 4857-sayili-is-kanunu.pdf)\n"
            "4. Eğer sağlanan dökümanlar içerisinde sorunun cevabı YOKSA, kesinlikle bilgi uydurma. "
            "Dürüstçe 'Sağlanan İK belgelerinde bu konuda bir bilgi bulunmamaktadır.' de ve hiçbir kaynak uydurma.\n"
            "5. Cevaplarında profesyonel, yapıcı ve kurumsal bir İK dili kullan.\n"
            "6. Yanıtını Türkçe olarak üret."
        )

        user_prompt = (
            f"Aşağıdaki dökümanları kullanarak soruyu yanıtla.\n\n"
            f"DÖKÜMANLAR:\n"
            f"{context_str}\n\n"
            f"KULLANICI SORUSU: {query}\n\n"
            f"HR COPILOT CEVABI:"
        )

        try:
            response = self.openai_client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2  # Low temperature for factual consistency
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI Chat API: {e}")
            return f"Üzgünüm, cevap oluşturulurken bir hata oluştu: {str(e)}"
