#!/usr/bin/env bash
# openai gpt4.1-mini prompt
# you are a senior developer write a git commit informaiton on this output git commit description in the style of conventional commits for github in English
OUT=changes_for_llm.txt

echo "=== Changed files ==="                 >  $OUT
git diff --name-status HEAD               >> $OUT
echo -e "\n=== Staged diff ==="            >> $OUT
git diff --cached                         >> $OUT
echo -e "\n=== Unstaged diff ==="          >> $OUT
git diff                                  >> $OUT

echo "Saved all changes to $OUT"
