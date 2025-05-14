#!/usr/bin/env bash
OUT=changes_for_llm.txt

echo "=== Changed files ==="                 >  $OUT
git diff --name-status HEAD               >> $OUT
echo -e "\n=== Staged diff ==="            >> $OUT
git diff --cached                         >> $OUT
echo -e "\n=== Unstaged diff ==="          >> $OUT
git diff                                  >> $OUT

echo "Saved all changes to $OUT"
