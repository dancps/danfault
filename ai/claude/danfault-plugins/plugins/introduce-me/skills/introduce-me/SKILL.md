---
name: introduce-me
description: |
  Introduce the user to a new topic (a concept, tool, or piece of code) in a fixed 4-section
  format. Use when the user says "introduce me to X" or asks for a first-contact overview of
  something new.
  Triggers: "introduce me to", "give me an intro to", "explain X to me from scratch"
user-invocable: true
argument-hint: <topic>
---

DRAFT — output format only, to be refined manually.

Produce the introduction as a single document with exactly these 4 sections, in this order.

## 1. Title of the thing
State the name of the topic as a heading, then three metadata lines:
- 1.1 Date: today's date
- 1.2 Keywords: 3-6 keywords for the topic

## 2. Pre-requisite knowledge
List the other concepts, ideas, or code the user should already know before this topic makes
sense. List them as numbered items (2.1, 2.2, 2.3, ...), no more than two short paragraphs of surrounding text.

## 3. Short explanation
One or two paragraphs, 500 characters at most, giving the compressed version of the topic.

## 4. Explanation
The full explanation. No more than two paragraphs.

## 5. What to learn next
List the other concepts, ideas, or code the user would like to learn after learning this topic. List them as numbered items (5.1, 5.2, 5.3, ...), no more than two short paragraphs of surrounding text.

After this, asks if the user wants to save this summary made by you or if it want more clarification about some point(user can reply with the item number)