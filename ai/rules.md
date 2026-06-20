# Qaydalar (Rules)

## R1  
**Məruzəçi Standartı**  
Zəng iştirakçılarını yalnız iki formada qeyd edin: 'Operator' (Bank tərəfi) və ya 'Müştəri' (Xidmət alan). Digər daxili kodlar və ya adlar ləğv edilməlidir.  

**Yanlış:** "Agent: Salam / Zəng edən: borcum var"  
**Doğru:** "Operator: Salam / Müştəri: borcum var"

## R2  
**Qrammatik Normalaşdırma**  
Şifahi ləhcələr rəsmi yazıya çevrilir. Əgər 'gələjəm, sənnən, gəlirsiz' deyirsə, 'gələcəm, səninlə, gəlirsiniz' şəklində yazın.  

**Yanlış:** "Müştəri: gələjəm, sənnən danışacam, gəlirsiz?"  
**Doğru:** "Müştəri: gələcəm, səninlə danışacam, gəlirsiniz?"

## R3  
**Rəqəmlər və Şəkilçilər**  
Rəqəm ifadələrini ardıcıl formata, ərəb rəqəmlərinə çevirin (iyirmi üç -> 23, iyirmi ikinci -> 22-ci). Səslənən şəkilçiləri mütləq defislə əlavə edin: 22-ci, 3-də.  

**Yanlış:** "iyirmi üç, iyirmi ikinci, üçdə"  
**Doğru:** "23, 22-ci, 3-də"

## R4  
**Qeyri-Söz Fraqmentləri və Kəkələmələr**  
Qeyri-söz fraqmentləri atılır. Kəkələmədə kəsik hissə real söz deyilsə yazılmır — yalnız tam söz qalır. Yalnız özünüdüzəltmədə hər iki hissə tam, mənalı söz olarsa saxlanılır.  

**Yanlış:** "pro proqrama qoşul, m-m-mən gəldim"  
**Doğru:** "Proqrama qoşul, Mən gəldim"

## R5  
**Tərəddüd Səsləri (Qapalı Siyahı)**  
Tərəddüd səsləri yalnız bu qapalı siyahıdan etiketlə verilir: [ıı], [ee], [hmm], [aa]. Mətndə plain 'ııı', 'ee' kimi yazılmır. Variantları bunlara yığın (eee/əə -> [ee], mmm -> [hmm]). 'hə, yox, aha' real sözlərdir — etiket deyil.  

**Yanlış:** "ııı mən eee karta baxım mmm"  
**Doğru:** "[ıı] mən [ee] karta baxım [hmm]"

## R6  
**Nitq Olmayan Hadisələr**  
Nitq olmayan hadisələr yalnız bu etiketlərlə verilir: [gülüş], [öskürək], [musiqi], [siqnal]. Tək başına olanda ayrıca seqment (text: '[musiqi]'), nitqin içində qısa olanda yerində yerləşdirilir. Nəfəs, fon küyü və xışıltı yazılmır.  

**Yanlış:** "(Nəfəs alır) [asqırıq] bəli (Xışıltı) doğrudur."  
**Doğru:** "Bəli [gülüş] doğrudur."

## R7  
**Anlaşılmayan və Çətin Sözlər**  
Səs-küy, sətir fasilələri və ya diksiya səbəbindən tamamilə anlaşılmaz olan sözləri təxmin etməyə çalışmayın. Bunun əvəzinə həmin hissəni '[unclear]' adlandırın və ayrıca vaxt möhürü kimi qeyd edin.  

**Yanlış:** "Küy səbəbindən başa düşülməyən sözü təxmin etmək"  
**Doğru:** "Müştəri: [unclear]"

## R8  
**Böyük Hərflər və Durğu İşarələri**  
Xüsusi isimləri və cümlə başlanğıclarını böyük hərflə yazın. İntonasiyadan asılı olaraq suallar '?' ilə, cümlələr isə '.' ilə bitməlidir. Təsadüfi durğu işarələri (,, və ya ??!!) istifadə etməyin.  

**Yanlış:** "salam... borcum nə gədərdi xanım??!!"  
**Doğru:** "Salam, borcum nə qədərdir xanım?"

## R9  
**Xarici Dillər və Alınma Sözlər**  
Bütün fraza rus və ya başqa dildədirsə ayrı sətirdə '[another_language]' yazılır. Cümlə içində işlənən tək alınma söz (karoçe, vobşe) isə Azərbaycan əlifbası ilə yazılır və cümlədə saxlanılır.  

**Yanlış:** "Müştəri: raboçi dindirildi da karoçe / Müştəri: [another_language] dindirildi da [another_language]"  
**Doğru:** "Müştəri: raboçi dindirildi da karoçe" və ya "Müştəri: [another_language]"

## R10  
**Maksimum Seqment Davamiyyəti**  
Start və end time arasındakı vaxt intervalı maksimum 30 saniyə olmalıdır.  

**Yanlış:** "start_time: 00:01, end_time: 00:45 (44 saniyə)"  
**Doğru:** "start_time: 00:01, end_time: 00:30 (29 saniyə)"