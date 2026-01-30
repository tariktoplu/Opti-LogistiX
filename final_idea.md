 Proje 2: "Opti-Logistix" (Sentetik Veri ile Dinamik Kaynak Önceliklendirme)


Hedeflenen Sorun: Deprem veya sel gibi geniş çaplı afetlerde, ambulans ve yardım araçlarının hasarlı yollar veya trafik nedeniyle hedefe ulaşamaması; sınırlı kaynakların (su, ilaç, iş makinesi) yanlış noktalara sevk edilmesi.

+3

AI Çözümü: Grafik Sinir Ağları (GNN) ve Pekiştirmeli Öğrenme (Reinforcement Learning) kullanarak "Hasar Öngörüsü ve Rota Optimizasyonu" yapan bir sistem. Yapay zeka, geçmiş afet verileri ve coğrafi bilgi sistemleri (GIS) verileriyle eğitilmiş sentetik senaryolar üzerinden, anlık yol durumuna göre en hızlı rotayı ve en acil ihtiyaç duyulan bölgeyi hesaplar.

+3


Paydaş Entegrasyonu: Belediyelerin yol durumu verileri ve Sağlık Müdürlüklerinin hastane kapasite verileriyle entegre çalışır. Mevcut AFAD yönetim yazılımını değiştirmek yerine, ona bir "karar destek katmanı" olarak eklenir.

+1


Operasyonel Etki: Lojistik gecikmeleri minimize eder, kaynak israfını önler ve yöneticilerin karmaşık veriler arasında boğulmadan hızlı karar vermesini sağlayan görsel paneller sunar.


bu nasıl yapılabilir ?

"Opti-Logistix" projesi, afet yönetiminde reaktif (olay olduktan sonra tepki veren) bir yapıdan proaktif (veriye dayalı öngörü yapan) bir yapıya geçişi simgeliyor. Bu çapta bir sistemi inşa etmek için akademik derinlik ile mühendislik pratiklerini birleştiren bir yol haritasına ihtiyacın var.

İşte bu projeyi hayata geçirmek için izleyebileceğin teknik ve operasyonel adımlar:
1. Mimari Yapı ve Veri Katmanı

Sistemin beyni, fiziksel dünyayı bir Graf (Ağ) yapısı olarak görmelidir. Şehirdeki her kavşak bir "düğüm" (node), her yol ise bir "kenar" (edge) olarak tanımlanır.

    Sentetik Veri Üretimi: Gerçek afet verisi kısıtlıdır. Bu yüzden GANs (Generative Adversarial Networks) kullanarak binlerce farklı deprem/sel senaryosu türetmelisin. "X şiddetinde depremde Y köprüsü çökerse trafik nasıl dağılır?" sorusunun yanıtı bu simülasyonlarda saklıdır.

    GIS Entegrasyonu: OpenStreetMap (OSM) veya Google Maps API üzerinden coğrafi verileri çekerek yükseklik, yol genişliği ve bina yoğunluğu gibi statik verileri modele eklemelisin.

2. Model Geliştirme: GNN ve RL Kombinasyonu

Bu projenin "mutfağı" iki ana yapay zeka disiplinini birleştirir:
A. Grafik Sinir Ağları (GNN) - Durum Analizi

GNN'ler, yol ağındaki mekânsal ilişkileri anlamak için mükemmeldir. Bir yolun kapanması sadece o noktayı değil, çevre yolları da etkiler.

    Görev: Hasar öngörüsü. Hangi yolların kapanma ihtimalinin en yüksek olduğunu (topolojik özelliklere bakarak) tahmin eder.

B. Pekiştirmeli Öğrenme (RL) - Dinamik Rotalama

RL ajanı, ambulans veya yardım tırı gibi davranır. Her adımda "En hızlı yol hangisi?" veya "Hangi bölgeye öncelik vermeliyim?" kararlarını verir.

    Ödül Fonksiyonu (R):
    R = -(t) + (\text{acil_seviyesi}) - (\text{risk_faktörü})

    Yani ajan, zamanı (t) minimize etmeye çalışırken, ulaştığı bölgenin aciliyetinden puan kazanır ve riskli (hasarlı) bölgelerden ceza alır.

3. Uygulama Adımları (Teknoloji Yığını)
Aşama	Kullanılacak Araçlar	Amaç
Simülasyon	SUMO (Simulation of Urban MObility)	Trafik ve araç hareketlerini simüle etmek.
Model	PyTorch Geometric	GNN mimarisini kurmak.
Karar Mekanizması	Ray Rllib veya Stable Baselines3	RL algoritmalarını (PPO, DQN) eğitmek.
Görselleştirme	Deck.gl veya Mapbox	Karar destek panelinde dinamik ısı haritaları oluşturmak.
4. Karar Destek Katmanı (Dashboard)

AFAD veya Belediye yetkilisi karmaşık kodlar görmemeli. Onlara şu üçlü akış sunulmalı:

    Tahmin: "Olası hasar nedeniyle A bölgesine ulaşım %40 riskli."

    Öneri: "Yardım tırlarını B rotasına yönlendirmek 12 dakika kazandırır."

    Kapasite: "X Hastanesi dolmak üzere, ambulansları Y Hastanesine sevk edin."

Kritik Başarı Faktörü: "Human-in-the-Loop"

Sistem tamamen otonom olmamalıdır. Yapay zeka bir öneri motoru olarak çalışmalı, son onay her zaman bir operatör tarafından verilmelidir. Bu, sistemin güvenilirliğini ve etik sorumluluğunu korur.

Bu projenin ilk prototipi için hangi şehri veya bölgeyi pilot alan olarak seçmeyi planlıyorsun? Buna göre veri seti ve topografya üzerine daha spesifik bir yol haritası çıkarabiliriz.