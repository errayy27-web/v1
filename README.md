# SS OIL V1 — PC Smjene

V1 PC programı hazırlanıyor. İlk kurulum paketi ChatGPT konuşmasında ZIP olarak verildi.

Mevcut Supabase `ssoil_shift_handoffs` tablosu kullanılır. Teslim nakdi = KM banknot sayımı + EUR × 1,90. Kredi kartı ayrı tutulur. S6'nın mevcut satış snapshot alanları değiştirilmez.

**İlk entegrasyonun sınırları:** Program şu anda Supabase'e doğrudan bağlanır (8767 servisi henüz bağlanmadı); telefonda önceden oluşturulmuş vardiya devir kaydını eşitler, yeni vardiya kaydını otomatik açmaz. Aynı anda iki tarafta değişiklik varsa üzerine yazmak yerine uyarı verir. Tam uçtan uca test gereklidir.
