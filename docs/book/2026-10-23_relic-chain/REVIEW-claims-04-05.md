04-search.md:72 | severe | says relic3 misses it because the name sits only in Bash commands; but our hit #1 is assistant text (20:42 today) so the reason is unproven | capture 31:3 | say relic3 returned 0 and the cause was not tested
04-search.md:94 | severe | says the two rows share no word with the question; row 1 has "api", "token", "model", row 2 has "token", "API" | capture 33:12,15 | say they share few words, or drop the claim
04-search.md:50 | minor | "top two scores 0.0164 and 0.0161"; the top two are both 0.0164, 0.0161 is the third row | capture 31:3-5 | write 0.0164, 0.0164 and 0.0161
05-report.md:51 | severe | "same prompt count, differs a hundredfold"; 1,073 vs 623 prompts are not equal, and per100 0.0 vs 313.6 has no ratio | capture 41:3,11 | say similar prompt counts give 0 to 313 commits per 100
05-report.md:5 | minor | "every command is a just recipe", but `node check.js` in 5.6 is not | capture 45:1 | say "nearly every command"
05-report.md:43 | minor | "the three most different rows" but `tail -12` shows only 12 of 40 rows; they are the most different of those 12, not of all | capture 41:1 | say "three rows from the tail"
05-report.md:110 | minor | "87% of notes match nothing asked"; unasked only means not closer to own prompts than to other oracles' | capture 43:3 | write "87% are closer to others' prompts"
05-report.md:129 | minor | "public version cut the private stuff"; capture shows only 994 vs 1,386 monthly values, not what was cut | capture 44:2-3 | say fewer values, the reason is by design not shown
05-report.md:157 | minor | "th has the same numbers so nothing missing" next to unexplained `errors 4`; the code block also shows only th lines | capture 45:7-8 | limit the claim to the card counts
