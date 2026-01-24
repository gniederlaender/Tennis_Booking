# Chat Mode - User Guide

## Overview

The Tennis Booking app now features a **conversational interface** (Chat Mode) that allows you to find and book tennis courts using natural language, just like chatting with a helpful assistant!

## Accessing Chat Mode

1. **From Classic Mode**: Click the "💬 Chat Mode" button in the header
2. **Direct URL**: Navigate to `/chat` in your browser
3. **Switch Back**: Click "Classic Mode" to return to the form-based interface

## How to Use

### Basic Conversations

Simply type what you want in plain English:

**Finding Courts:**
- "Find a court tomorrow at 6pm"
- "I want to play tennis next Monday evening"
- "Show available courts this weekend"
- "Search for courts on Friday between 17:00 and 19:00"

**Finding Trainers:**
- "I need a trainer tomorrow morning"
- "Find trainer Tobias on Friday"
- "Show me trainers next Monday at 10:00"

**Booking:**
- "Book option 1"
- "I'll take the first one"
- "Reserve number 2"
- "Book it"

**Other Commands:**
- "Help" - Show examples
- "Hello" or "Hi" - Start fresh conversation
- "Thanks" - Polite acknowledgment
- "Clear conversation" - Reset (via button)

### Sample Conversation

**Example 1: Quick Court Booking**

> **You:** Find a court tomorrow at 18:00
>
> **Assistant:** Great! I found 8 available courts for Wednesday, January 22.
>
> 1. **Platz 3 HALLE** at Arsenal
>    Wednesday, January 22 at 18:00 (€26)
>
> 2. **Platz 5 HALLE** at Arsenal
>    Wednesday, January 22 at 19:00 (€26)
>
> 3. **Platz 2 HALLE** at Arsenal
>    Wednesday, January 22 at 18:30 (€26)
>
> Which one would you like to book?
>
> **You:** Book option 1
>
> **Assistant:** ✓ Booked! Successfully booked Platz 3 HALLE at Arsenal for Wednesday, Jan 22 at 18:00. See you on court! 🎾

**Example 2: Trainer Search**

> **You:** I need a trainer next Monday morning
>
> **Assistant:** Great! I found 5 available trainer sessions for Monday, January 27:
>
> 1. **TOBIAS W.**
>    Monday, January 27, 09:00-10:00 (€66)
>
> 2. **ROSSEN**
>    Monday, January 27, 09:00-10:00 (€66)
>
> Which time works for you?
>
> **You:** First one please
>
> **Assistant:** Trainer booking is not yet automated. Please contact Arsenal directly to book this session:
>
> **TOBIAS W.**
> 2026-01-27 at 09:00-10:00

## Features

### Smart Intent Recognition

The assistant understands various ways of expressing the same intent:

- **Search**: "find", "search", "show", "available", "I want", "need"
- **Book**: "book", "reserve", "I'll take", "yes"
- **Info**: "history", "bookings", "what did I"

### Context Awareness

The chat remembers your conversation:

- After showing results, you can just say "book option 1" without repeating details
- References like "the first one", "option 2", "number 3" work correctly
- Conversation state is maintained throughout your session

### Quick Suggestions

After each message, the assistant provides clickable suggestion buttons for common next steps:

- "Book option 1", "Book option 2"
- "Show more"
- "Different time"
- "Find a court", "Find a trainer"

Just click a suggestion instead of typing!

### Visual Feedback

- **Typing indicator**: Three animated dots show when the assistant is "thinking"
- **Message bubbles**: Your messages appear on the right (blue), assistant on the left (gray)
- **Auto-scroll**: Chat automatically scrolls to show the latest message
- **Markdown**: Bold (**text**) and italic (_text_) formatting supported

## Technical Details

### What It Understands

**Time expressions:**
- Relative: "tomorrow", "next Monday", "this weekend"
- Specific: "January 24", "7.1.2026"
- Time ranges: "morning", "afternoon", "evening"
- Exact times: "at 18:00", "6pm", "between 15:00 and 18:00"

**Locations:**
- "Arsenal" or "Das Spiel" → Das Spiel (Tenniszentrum Arsenal)
- "Post SV" → Post SV Wien
- No location specified → searches both

**Trainers:**
- "Tobias" or "Tobias W" → Trainer Tobias W.
- "Rossen" → Trainer Rossen

**Slot references:**
- "option 1", "option 2", etc.
- "first one", "second one", "third one"
- "number 1", "number 2"
- Just "1", "2", "3"

### Session Management

- Your conversation is stored in your browser session
- Lasts for the duration of your login
- Click "Clear conversation" to start fresh
- Each user has their own independent chat session

### Integration with Existing Features

Chat Mode uses the **same backend** as Classic Mode:

- ✓ Natural language timeframe parsing
- ✓ Real-time availability checking
- ✓ Preference learning (PREFERRED slots)
- ✓ Automatic booking system
- ✓ Booking history logging

Everything you can do in Classic Mode works in Chat Mode!

## Tips for Best Results

1. **Be specific about time**: Include both date and time for best results
   - Good: "tomorrow at 18:00"
   - Less good: "tomorrow" (will ask for clarification)

2. **Use numbers for booking**: "book option 1" is clearer than "book that one"

3. **One request at a time**: Ask for courts OR trainers, not both in one message

4. **Use suggestions**: Click the suggestion buttons for common actions

5. **Type naturally**: Don't worry about perfect grammar, the assistant understands casual language

## Limitations

- **Trainer booking**: Currently shows availability but doesn't auto-book (contact Arsenal directly)
- **Booking history**: Not yet integrated into chat (coming soon)
- **Multi-turn clarification**: Limited to basic missing info (date/time)
- **No voice input**: Text-only for now (voice coming in future)

## Troubleshooting

**Assistant doesn't understand:**
- Try rephrasing with simpler language
- Use the "Help" command to see examples
- Check that you included date and time for searches

**Booking fails:**
- The slot may have been taken by someone else
- Try a different option from the results
- Switch to Classic Mode as a fallback

**Session lost:**
- If you see "no search results", you may need to search again
- Use "Clear conversation" to start fresh

**Not showing results:**
- Make sure you're logged in
- Check that the date/time is in the future
- Try Classic Mode to verify the backend is working

## Feedback

This is Phase 1 (MVP) of the conversational interface! Future enhancements planned:

- Better natural language understanding (AI/LLM integration)
- Voice input/output
- Booking history in chat
- Multi-language support
- Proactive suggestions based on your schedule

Enjoy chatting with your tennis booking assistant! 🎾

---

**Quick Start:**
1. Navigate to `/chat` or click "💬 Chat Mode"
2. Type: "Find a court tomorrow at 6pm"
3. Click "Book option 1"
4. Done! 🎾
