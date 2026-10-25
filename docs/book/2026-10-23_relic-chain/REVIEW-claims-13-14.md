13-vs.md:3 | severe | "ทั้งปีถูกอ่านสองรอบแล้ว" presents the comparison as complete; z.ai 15m lane was still running (8,925 of 15,437) | capture 150:15m | say "ทั้งปีอ่านสองรอบ ยกเว้น 15m ของ z.ai ที่ยังไม่จบ"
13-vs.md:93 | severe | says opening counts the start of "focus"; vs.py opening counts the first four words of the `en` field | vs.py:101 | change "ขึ้นต้น focus" to "ขึ้นต้นช่อง en"
13-vs.md:104 | severe | "ไม่รู้ว่า the person คือ Nat" is a guess about the model's reason, not shown by capture 152 | capture 152:15m | write "ไม่ใช่ชื่อ Nat" or label it as a guess
13-vs.md:108 | severe | "z.ai เรียกขนาดถูกทุกครั้ง" is not shown; capture 152 lists only top-3 openings (24% max at 15m) | capture 152:3h,1h,15m | write "ในวลีขึ้นต้นสามอันดับแรก z.ai เรียกขนาดถูก"
13-vs.md:140 | severe | example is not typical: vs.py example picks the first 2026-06-10 window where types differ and only z.ai names friction, so "ตัวอย่างของ 96% กับ 14%" and the cause "none ทุกครั้งที่ไม่เห็น" are unsupported | vs.py:138 | say it was picked for the gap
14-friction.md:32 | severe | "z.ai ไม่เคยตอบ none"/"ครบทุกหน้าต่าง" contradicts: only-gb300 11 + neither 10 = 21 windows where z.ai gave none (0.2%, rounds to 0%) | capture 154:lesson | "แทบไม่เคย (21 จาก 8,925)"
14-friction.md:58 | severe | "fix มีแค่ 991" misreads a count as a rate; gb300 labels fix ~11% of 15m (about 980 windows), so nearly every fix window has z.ai friction | capture 150:15m, 154:last | compare with each type's total
13-vs.md:36 | minor | "เร็วกว่าสิบเท่า": D6 medians show 20-27x (2.7 vs 54.9 s); only trial shows 9x | D6-vs.txt:15m | write "สิบถึงยี่สิบกว่าเท่า"
13-vs.md:36 | minor | "ช้าและแพงกว่า": no capture shows any cost of z.ai | capture 151 | drop "แพง" or cite a source
13-vs.md:81 | minor | repeats itself: "gb300 ตอบ build 72% ส่วน z.ai แค่ 42%" then "gb300 ตอบ build 72% ... z.ai ตอบ build 42%" in the next sentence | capture 150:day | cut the second
13-vs.md:106 | minor | repeats the lines before it: 1h "The day was spent" 69% and 15m "The person spent 15" 66% are stated twice in a row | capture 152:1h,15m | delete the second paragraph
13-vs.md:55 | minor | "ช้ากว่าสองเท่า" is vs qwen3:14b (13.6 vs 6.8) but is placed after Nemotron (4.5, 3x) | capture 151 | name the baseline
14-friction.md:30 | minor | "ถ้าเจอเมื่อมี ก็ยาวต่างกันด้วย" is garbled Thai | capture 154:3 | "ตอนที่เจอ z.ai ก็เขียนยาวกว่า"
