# Python 3 "Black Hat Python" Kaynak Kodu

Justin Seitz'in "Black Hat Python" kitabındaki kaynak kodlar. Kodlar tamamen Python 3'e dönüştürüldü, PEP8 standartlarına uyacak şekilde yeniden biçimlendirildi ve kullanımdan kalkan kütüphanelerden kaynaklanan sorunların ortadan kaldırılması için yeniden düzenlendi.

Kitap boyunca sunulan kaynak kodlarında pek çok iyileştirme yapılabilecek olsa da, okuyucuların kitapta gördüğü şekilde uygulayabilmesi için, kodlar mümkün olduğunca değiştirilmeden bırakılmıştır. Kodlar, bu haliyle bile "docstring"lerden "type hinting" ve "exeption handling"e kadar bazı ciddi düzenlemelere ihtiyaç duyuyor ki içerik yöneticileri gibi geliştirmelerden bahsetmiyorum bile. Ancak bu sorunlar, okuyucu bunları uygulamaya niyetliyse kendi başlarına fayda sağlayabilir. Ayrıca, programın çalışması sırasında ortaya çıkan önemli hatalar engellenmek isteniyorsa, düzeltilmiş olan girintilerden kaynaklanan birçok hatayı da gösteriyor.
 
*Buna benzer bir çeviri, TJ O'Connor tarafından yazılan "Violent Python" kitabının kaynak kodunda da yapılıp kullanıma sunulmuştur. Henüz bakmadıyanız [buraya](https://github.com/EONRaider/violent-python3) göz atabilirsiniz.*

## Nasıl Kullanılır?
Projeyi `git clone` kullanarak klonlayacağınız dizini (DIR) seçin, bunun için yeni sanal bir ortam veya `venv` oluşturmanız önerilir. Ardından `pip install` kullanarak gereksinimleri yükleyin.

```
user@host:~/DIR$ git clone https://github.com/EONRaider/blackhat-python3
user@host:~/DIR$ python3 -m venv venv
user@host:~/DIR$ source venv/bin/activate
(venv) user@host:~/DIR$ pip install -r requirements.txt
```

## Notlar
- Kitapta sunulan bazı listeler, yazarın "No Starch Press" web sitesinde bulunan kod deposunda eksikti ama artık ilgili bölümlere eklendi. Dosyalara, kitapta sunulan kodlarla bağlantı kurulabilmesi için, daha doğru bir isimlendirme yapıldı.
- Derleyici tarafından uyarılara sebep olan küçük hatalı kodlar, özellikleri değiştirilmeden düzeltildi.
- Kodların çalışması için gerekli olan yardımcı dosyalar, ilgili bölümlere eklendi.
- Kişisel bir not olarak, yazarın etik hacker standartları için gerekli olan çalışma hızını riske atmadan, daha temiz kod yazması mümkün olabilirdi. Neden bunu yapmamayı tercih ettiği bilinmiyor.

## Yeniden Düzenlenenler
Kaynak kodunu düzgün bir şekilde çalıştırmak ve önemli hatalardan korunmak için yapılan kritik hata düzeltmeleri:
- `chapter02/bh_sshserver.py` dosyasının, `test_rsa.key` dosyasında bulunan RSA anahtarına ihtiyacı varken artık ilgili dizine dahil edilmiştir.
- `chapter03/sniffer_ip_header_decode.py` & `sniffer_with_icmp.py` & `scanner.py` dosyalarında, `struct` çalıştırılmasındaki sorunlar nedeniyle IP paket boyutlarının ve 32/64-bit mimariler arasında taşınabilirliğin tanımlanmasında ciddi sorunlar vardı. Stack Overflow'daki [bu başlıkta](https://stackoverflow.com/questions/29306747/python-sniffing-from-black-hat-python-book#29307402) bu sorunlar hakkında daha fazla bilgi edinebilirsiniz.
- `chapter03/scanner.py`, artık güncellenmeyen ve Python 3 ile pek çok uyumsuzluğa sahip olan `netaddr` kitaplığını kullanıyordu. Bu nedenle kod yeniden düzenlendi ve şimdi Python'un `stdlib` kütüphanesindeki `ipaddress` modülünü kullanıyor.
- `chapter04/arper.py` & `mail_sniffer.py`, Python 3 ile uyumlu olmayan `scapy` kitaplığını kullanıyordu. Bu nedenle kodlar yeniden düzenlendi ve artık `kamene` kitaplığını kullanılıyor.
- `chapter04/pic_carver.py` artık `cv2` yerine `opencv-python` kitaplığını kullanıyor. "cv2" modülü kullanımdan kaldırıldı ve yenisiyle değiştirildi. Orijinal koddaki "cv2.cv.CV_HAAR_SCALE_IMAGE" parametresi, [bu commit](https://github.com/ragulin/face-recognition-server/commit/7b9773be352cbcd8a3aff50c7371f8aaf737bc5c) nedeniyle "cv2.CASCADE_SCALE_IMAGE" olarak değiştirildi.
- `chapter05/content_bruter.py` dosyası çalışmak için bir wordlist gerektiriyordu. Bu ihtiyaç, `all.txt` altındaki bölüme eklendi.
- `chapter05/joomla_killer.py` dosyası da çalışmak için bir wordlist gerektiriyordu. Bu ihtiyaç, `cain.txt` altındaki bölüme eklendi.
- `chapter06/bhp_bing.py` & `bhp_fuzzer.py` & `bhp_wordlist.py`, PEP8 ile uyumlu olacak şekilde yeniden biçimlendirildi. Ancak Burp Suite'teki bu özel uygulamada sınıf adlarının "camel-casing"e uyması gerekliliği nedeniyle uyarılar yine de gösterilecektir.
- `chapter06/jython-standalone-2.7.2.jar`, aynı dosyanın kitapta sunulana göre daha güncel bir versiyonudur.
- `chapter07/git_trojan.py`dosyasındaki `types`, artık kullanımdan kaldırılmış olan `imp` kitaplığının yerini alacak şekilde yeniden düzenlendi. Kitapta anlatıldığı gibi, gerekli konfigürasyon dosyalarını içeren bir alt dizin (subdirectory) yapısı uygulanmıştır. "trojan_config" değişkeninde `config` alt dizinine giden göreli yol eksikti. Orijinal kod tarafından oluşturulan bir AttributeError hatasını önlemek için 60. satıra "to_tree" yöntemine bir kod eklendi. İki adımlı doğrulama kullanılması durumunda kişinin şifresini kullanmak yerine bir "access token"ın nasıl oluşturulacağına ilişkin talimatlar yorum olarak eklendi.
- `chapter08/keylogger.py`, `PyHook` kitaplığının çalışmasını gerektiriyor. 1.6.2 sürümüyle birlikte bir "wheel" dosyası eklenmiştir. Gerekirse diğer sürümler [buradan](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyhook) indirilebilir.
- `chapter09/ie_exfil.py`, açık metin değişkeninin (string veya binary olarak görünebilen) "encrypt_string" işlevine dönüştürülmesiyle hatalar düzeldi. Ek olarak, `base64` kütüphanesinin kullanımı düzeltildi. *[Bu commit'te](https://github.com/EONRaider/blackhat-python3/pull/2/commits/fcab6afc19fc4ea01b8c5c475e7b8c5e4b158df6) [Enraged](https://github.com/Enraged) tarafından katkı sağlandı.*

## Çeviriler
Diğer dillere yapılan çevirileri buradan kontrol edebilirsiniz:
- [Bedirhan Budak](https://github.com/bedirhanbudak) tarafından [Turkish](https://github.com/EONRaider/blackhat-python3/tree/turkish-language) diline çevrilmiştir.

## Katkıda Bulunmak İsteyenler
Sağduyulu olmak için, önce bu repository'de yapmak istediğiniz değişikliği bir "issue" aracılığıyla tartışmaya çalışın.

1. Gerçekleştirmek istediğiniz değişiklikler için bir "pull request" açtığınızdan emin olun. Eğer bir veya iki satır değişecekse, "issue" üzerinden talep edilmelidir.
2. Eğer gerekliyse, README.md dosyasını proje yapısındaki değişikliklerle ilgili ayrıntılarla güncelleyin.
3. Değişiklikleri içeren commit mesajlarının bir standarda uyduğundan emin olun. Nasıl devam edeceğinizi bilmiyorsanız, [buradan](https://chris.beams.io/posts/git-commit/) nasıl yapılacağına dair bilgi alabilirsiniz.
4. Talebiniz, mümkün olan en kısa sürede (genellikle 48 saat içinde) incelenecektir.
