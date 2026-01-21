# Conversational Interface Concept for Tennis Booking App

**Version:** 1.0
**Date:** January 21, 2026
**Status:** Conceptual Design

---

## Executive Summary

This document outlines a concept for transforming the Tennis Booking Finder into a conversational interface that feels like ChatGPT or Claude, but focused solely on finding and booking tennis courts and trainers in Vienna. The interface will leverage existing functionality (timeframe parsing, court/trainer search, booking, preference learning) wrapped in a natural conversation flow.

---

## 1. Vision & User Experience

### Core Interaction Model

Instead of filling forms, users have a natural conversation:

**Example 1: Simple Court Booking**

> **User:** "I want to play tennis tomorrow evening"
>
> **Assistant:** "I'll help you find tennis courts for tomorrow evening. Let me search for available slots between 18:00-20:00...
>
> Great! I found 8 available courts for tomorrow (Wednesday, January 22) in the evening:
>
> 1. ⭐ **PREFERRED** - Platz 3 HALLE at Arsenal - 18:00 (€26)
> 2. Platz 5 HALLE at Arsenal - 19:00 (€26)
> 3. Platz 2 HALLE at Arsenal - 18:30 (€26)
>
> Based on your history, you usually prefer Arsenal in the evening. Would you like to book the first option, or see more?"
>
> **User:** "Book option 1"
>
> **Assistant:** "Perfect! I'm booking Platz 3 HALLE at Arsenal for tomorrow (Jan 22) at 18:00... ✓ Done! Your court is booked. You'll receive a confirmation. See you on court! 🎾"

**Example 2: Trainer Search**

> **User:** "I need a tennis trainer next Monday morning, preferably Tobias"
>
> **Assistant:** "Let me search for trainer availability on Monday morning...
>
> Good news! Tobias W. is available:
>
> 1. Monday, Jan 27 - 09:00-10:00 (€66)
> 2. Monday, Jan 27 - 10:00-11:00 (€66)
> 3. Monday, Jan 27 - 11:00-12:00 (€66)
>
> Which time works best for you?"
>
> **User:** "9am sounds good"
>
> **Assistant:** "Great choice! Booking your session with Tobias W. on Monday, Jan 27 at 09:00... ✓ Booked! Your training session is confirmed. Have a great lesson!"

**Example 3: Clarification & Context**

> **User:** "Find me a court"
>
> **Assistant:** "I'd be happy to help! When would you like to play? For example, you could say 'tomorrow afternoon' or 'next Friday at 17:00'."
>
> **User:** "This Friday 6pm"
>
> **Assistant:** "Searching for courts on Friday, January 24 at 18:00...
>
> Found 12 available courts! Would you like me to show you:
> - Only Arsenal courts
> - Only Post SV courts
> - Both locations (default)"
>
> **User:** "Just Arsenal"
>
> **Assistant:** [Shows Arsenal results...]

**Example 4: Follow-up Conversations**

> **User:** "What did I book last week?"
>
> **Assistant:** "Looking at your booking history... You booked Platz 5 HALLE at Arsenal on January 14 at 19:00. Would you like to book the same slot again?"
>
> **User:** "Yes, for next Tuesday"
>
> **Assistant:** "Searching for Platz 5 HALLE at Arsenal on Tuesday, Jan 28 at 19:00... ✓ Available! Should I book it?"

---

## 2. Conversational Capabilities

### Natural Language Understanding

The assistant should understand:

1. **Time Expressions**
   - Relative: "tomorrow", "next Monday", "this weekend"
   - Specific: "January 24", "7.1.2026"
   - Time ranges: "morning" (7-12), "afternoon" (12-17), "evening" (17-22)
   - Exact times: "at 18:00", "6pm", "between 15:00 and 18:00"

2. **Intent Recognition**
   - Search: "find", "search", "look for", "show me", "I want to"
   - Book: "book", "reserve", "I'll take", "yes book it"
   - Cancel: "never mind", "cancel", "change my mind"
   - Info: "what are my bookings", "show history", "what's available"
   - Preferences: "I prefer", "usually I", "my favorite"

3. **Entity Extraction**
   - Court vs Trainer
   - Location (Arsenal, Post SV)
   - Trainer name (Tobias, Rossen, etc.)
   - Court number (Platz 1, Platz 5)
   - Date/time
   - Duration (1 hour, 2 hours)

4. **Context Awareness**
   - Remember previous searches in session
   - Reference "option 1", "the first one", "that court"
   - Understand "same as last time", "my usual"
   - Track conversation state

---

## 3. Technical Architecture

### System Components

```
┌─────────────────────────────────────────────┐
│         Conversational Interface            │
│  (Chat UI + Message History Display)        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│      Conversation Manager                   │
│  - Intent Classification                    │
│  - Entity Extraction                        │
│  - Context Tracking                         │
│  - Response Generation                      │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌────────▼──────────┐
│ Intent Router  │   │  Context Store    │
│  (Actions)     │   │  (Session State)  │
└───────┬────────┘   └───────────────────┘
        │
        ├─────► Search Courts (existing: scrapers_v2.py)
        ├─────► Search Trainers (existing: trainer_finder.py)
        ├─────► Book Court/Trainer (existing: booking.py)
        ├─────► Parse Time (existing: timeframe_parser.py)
        ├─────► Get Preferences (existing: preference_engine.py)
        └─────► Booking History (existing: booking.py)
```

### API Endpoints

**New Endpoints:**

```python
# Conversational interface
POST /api/chat
{
    "message": "I want to play tennis tomorrow evening",
    "session_id": "abc123",
    "context": {...}
}

Response:
{
    "reply": "I'll help you find tennis courts...",
    "action": "search_courts",
    "results": [...],
    "suggestions": ["Book option 1", "Show more", "Different time"],
    "context": {...}
}

# Get conversation history
GET /api/chat/history?session_id=abc123

# Clear context
DELETE /api/chat/session/{session_id}
```

**Reuse Existing Endpoints:**
- `/search` - Court/trainer search
- `/book` - Booking functionality
- Existing authentication

---

## 4. Implementation Approach

### Phase 1: Basic Conversational UI (MVP)

**What:** Chat interface with rule-based intent detection

**Components:**
1. **Chat UI**
   - Message bubble layout (user/assistant)
   - Input field at bottom
   - Typing indicators
   - Auto-scroll to latest message

2. **Simple Intent Router**
   - Keyword matching for intents:
     - "find", "search" → search intent
     - "book", "reserve" → booking intent
     - "trainer" → trainer mode
     - "history", "bookings" → history intent
   - Use existing timeframe_parser for dates

3. **Response Templates**
   - Hardcoded templates for common scenarios
   - Inject search results into templates
   - Format results as conversational text

**Tech Stack:**
- Frontend: Vanilla JS (keep it simple)
- Backend: New Flask route `/api/chat`
- Session: Store context in Flask session
- No AI/LLM needed for MVP

**Estimated Effort:** 2-3 days

---

### Phase 2: Enhanced NLU (Natural Language Understanding)

**What:** Better intent recognition and entity extraction

**Components:**
1. **Intent Classifier**
   - Simple ML model or rule-based NLU library
   - Options:
     - spaCy for entity extraction
     - Rasa NLU (open source)
     - Simple keyword + pattern matching

2. **Entity Extractor**
   - Extract: date, time, location, trainer name, court number
   - Use existing timeframe_parser + regex patterns
   - Build entity dictionary (trainer names, venues)

3. **Context Manager**
   - Track conversation state
   - Store last search results
   - Remember user preferences
   - Handle pronouns ("it", "that one")

4. **Multi-turn Conversations**
   - Handle follow-up questions
   - Clarification requests
   - Confirmation dialogs

**Tech Stack:**
- spaCy or simple pattern matching
- SQLite for session storage
- Redis (optional) for faster session access

**Estimated Effort:** 1 week

---

### Phase 3: LLM Integration (Advanced)

**What:** Use actual LLM for natural conversation

**Options:**

**Option A: Claude API (Recommended)**
- Use Claude API for intent understanding
- Provide system prompt defining the assistant's role
- Pass available functions (search, book) to Claude
- Let Claude generate natural responses
- Pros: Best conversational quality, handles edge cases
- Cons: API costs, requires internet

**Option B: Local LLM**
- Run small local model (Llama 3 8B, Phi-3)
- Fine-tune on tennis booking conversations
- Pros: No API costs, privacy
- Cons: Requires GPU, slower, quality lower than Claude

**Option C: Hybrid**
- Use Claude for understanding + response
- Use local rules for actions (search, book)
- Best of both worlds

**Implementation:**
```python
# System prompt for Claude
SYSTEM_PROMPT = """
You are a tennis court booking assistant for Vienna. Your sole purpose is to help users:
1. Find available tennis courts at Arsenal (Das Spiel) and Post SV Wien
2. Find available trainers at Arsenal
3. Book courts and trainer sessions
4. Check booking history

You have access to these functions:
- search_courts(date, start_time, end_time, locations)
- search_trainers(date, start_time, end_time, trainer_name)
- book_court(slot_id)
- get_booking_history(user_id)

Be friendly, concise, and sports-enthusiastic. Use tennis emojis 🎾 occasionally.
"""
```

**Estimated Effort:** 1 week (Claude API), 2-3 weeks (local LLM)

---

### Phase 4: Advanced Features

**Quick Actions:**
- "Book my usual slot" (use preference engine)
- "Find me anything tomorrow" (smart search)
- "Cancel my next booking"

**Smart Suggestions:**
- "You usually play on Wednesdays at 18:00, want to search?"
- "Tobias has an opening at your preferred time"
- "Platz 5 (your favorite) just became available"

**Voice Interface:**
- Add speech-to-text input
- Text-to-speech responses
- Mobile-friendly

**Multi-modal:**
- Show calendar view alongside chat
- Click on calendar to add to conversation
- Mixed UI: chat + visual elements

---

## 5. UI/UX Design Concept

### Chat Interface Layout

```
┌────────────────────────────────────────────────┐
│  🎾 Tennis Booking Assistant        [user] [≡] │
├────────────────────────────────────────────────┤
│                                                │
│  ┌──────────────────────────────────────┐     │
│  │ Hi! I'm your tennis booking          │     │
│  │ assistant. I can help you find       │     │
│  │ courts and trainers in Vienna.       │     │
│  │ What would you like to do?           │     │
│  └──────────────────────────────────────┘     │
│                                        [10:23] │
│                                                │
│                            ┌──────────────┐   │
│                            │ Find a court │   │
│                            │ tomorrow     │   │
│                            │ evening      │   │
│                            └──────────────┘   │
│                                    [10:24]     │
│                                                │
│  ┌──────────────────────────────────────┐     │
│  │ Searching for courts tomorrow        │     │
│  │ evening (Jan 22, 18:00-20:00)...     │     │
│  │                                      │     │
│  │ Found 8 courts! Here are top 3:      │     │
│  │                                      │     │
│  │ ⭐ 1. Platz 3 HALLE - Arsenal        │     │
│  │    Tomorrow 18:00 (€26)              │     │
│  │    [Book Now]                        │     │
│  │                                      │     │
│  │ 2. Platz 5 HALLE - Arsenal           │     │
│  │    Tomorrow 19:00 (€26)              │     │
│  │    [Book Now]                        │     │
│  │                                      │     │
│  │ [Show all 8 results]                 │     │
│  └──────────────────────────────────────┘     │
│                                        [10:24] │
│                                                │
│                            ┌──────────────┐   │
│                            │ Book the     │   │
│                            │ first one    │   │
│                            └──────────────┘   │
│                                    [10:25]     │
│                                                │
│  ┌──────────────────────────────────────┐     │
│  │ ✓ Booked! Platz 3 HALLE at Arsenal   │     │
│  │   Tomorrow, Jan 22 at 18:00          │     │
│  │                                      │     │
│  │   Booking ID: #BK123456              │     │
│  │   See you on court! 🎾               │     │
│  └──────────────────────────────────────┘     │
│                                        [10:25] │
│                                                │
│ ┌──────────────────────────────────────────┐  │
│ │ Type a message...                    [🎤]│  │
│ └──────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

### Quick Actions Bar

Below the input field:

```
┌────────────────────────────────────────────────┐
│ Quick actions:                                 │
│ [Find court] [Find trainer] [My bookings]     │
│ [Tomorrow evening] [This weekend]             │
└────────────────────────────────────────────────┘
```

### Message Types

1. **Text Messages** - Simple back and forth
2. **Card Messages** - Court/trainer results in cards
3. **List Messages** - Multiple options numbered
4. **Action Buttons** - Quick reply buttons
5. **Confirmation** - Yes/No buttons
6. **Status Messages** - Loading, success, error

---

## 6. Conversational Flows

### Flow 1: Court Search → Book

```
State: IDLE
User: "Find court tomorrow 6pm"
  → Parse: {intent: search_court, date: tomorrow, time: 18:00}
  → Action: search_courts()
  → State: RESULTS_SHOWN
Assistant: "Found 8 courts, here are top 3..."

State: RESULTS_SHOWN
User: "Book option 1"
  → Parse: {intent: book, reference: option_1}
  → Action: book_court(results[0])
  → State: BOOKING_CONFIRMED
Assistant: "✓ Booked! See you on court 🎾"

State: BOOKING_CONFIRMED
User: "Thanks!"
  → State: IDLE
Assistant: "You're welcome! Anything else?"
```

### Flow 2: Clarification Dialog

```
State: IDLE
User: "Find me a trainer"
  → Parse: {intent: search_trainer, date: missing, time: missing}
  → State: NEEDS_CLARIFICATION
Assistant: "Sure! When would you like the session?"

State: NEEDS_CLARIFICATION
User: "Monday morning"
  → Parse: {date: next_monday, time: morning}
  → Action: search_trainers()
  → State: RESULTS_SHOWN
Assistant: "Found 3 trainers available Monday morning..."
```

### Flow 3: Error Handling

```
State: IDLE
User: "Book the best court"
  → Parse: {intent: book, reference: undefined}
  → State: ERROR
Assistant: "I don't have any search results yet. Would you like me to search for courts first?"

User: "Yes, tomorrow evening"
  → Parse: {intent: search_court, date: tomorrow, time: evening}
  → Action: search_courts()
  → State: RESULTS_SHOWN
```

---

## 7. Data Model

### Conversation Session

```python
{
    "session_id": "abc123",
    "user_id": 42,
    "created_at": "2026-01-21T10:00:00Z",
    "last_active": "2026-01-21T10:25:00Z",
    "context": {
        "state": "RESULTS_SHOWN",
        "last_intent": "search_court",
        "last_search": {
            "type": "court",
            "date": "2026-01-22",
            "time": "18:00",
            "locations": ["arsenal"],
            "results": [...]  # Cached results
        },
        "pending_action": null,
        "conversation_history": [
            {
                "role": "user",
                "message": "Find court tomorrow 6pm",
                "timestamp": "2026-01-21T10:23:00Z"
            },
            {
                "role": "assistant",
                "message": "Found 8 courts...",
                "timestamp": "2026-01-21T10:24:00Z",
                "metadata": {
                    "action": "search_courts",
                    "result_count": 8
                }
            }
        ]
    }
}
```

---

## 8. Response Generation Templates

### Template Examples

```python
TEMPLATES = {
    "search_results": {
        "court": "I found {count} available courts for {date} at {time}:\n\n{results}\n\nWhich one would you like to book?",
        "trainer": "Great! {count} trainers are available:\n\n{results}\n\nWhich time works for you?",
        "no_results": "Sorry, I couldn't find any {type} for {date} at {time}. Would you like to try a different time?",
    },
    "booking": {
        "confirm": "Should I book {court} at {venue} on {date} at {time}?",
        "success": "✓ Booked! {court} at {venue} on {date} at {time}. See you on court! 🎾",
        "error": "Oops! Booking failed: {error}. Would you like to try a different slot?",
    },
    "clarification": {
        "missing_time": "When would you like to play? For example: 'tomorrow at 18:00' or 'next Monday evening'",
        "missing_date": "Which day? You can say 'tomorrow', 'next Friday', or a specific date.",
        "confirm_location": "Where would you like to play?\n- Arsenal (Das Spiel)\n- Post SV Wien\n- Both",
    },
    "greeting": {
        "first": "Hi! I'm your tennis booking assistant. I can help you find and book courts and trainers in Vienna. What would you like to do?",
        "returning": "Welcome back! Ready to find your next court? Just tell me when you'd like to play.",
    }
}
```

---

## 9. Advantages Over Current Form UI

### User Benefits

1. **Natural**: Talk like you would to a friend
2. **Faster**: No clicking through forms
3. **Flexible**: Ask in any format
4. **Contextual**: Remember your preferences
5. **Forgiving**: Handles vague requests
6. **Helpful**: Suggests based on history

### Developer Benefits

1. **Leverage existing code**: All backend functionality reused
2. **Extensible**: Easy to add new intents
3. **Maintainable**: Centralized conversation logic
4. **Testable**: Clear state machine

---

## 10. Limitations & Challenges

### Technical Challenges

1. **Intent Ambiguity**
   - "book" could mean search or reserve
   - Solution: Track state, ask for confirmation

2. **Entity Extraction**
   - "next Monday" - which Monday?
   - Solution: Use existing timeframe_parser.py

3. **Context Loss**
   - User says "the first one" - which result?
   - Solution: Store last results in session

4. **Error Recovery**
   - What if booking fails mid-conversation?
   - Solution: Clear error messages, retry options

### UX Challenges

1. **Typing Friction**
   - Users might prefer clicking
   - Solution: Hybrid UI with quick action buttons

2. **Discovery**
   - Users don't know what to ask
   - Solution: Suggestions, examples, quick actions

3. **Long Results**
   - 50 available courts - how to present?
   - Solution: Show top 3, offer "show more"

4. **Mobile**
   - Typing on mobile is hard
   - Solution: Voice input, predefined buttons

---

## 11. Rollout Strategy

### Phase 1: Experiment (Week 1-2)
- Build alongside existing form UI
- Add "Try Chat Mode" button
- Collect user feedback
- Track metrics: usage, completion rate

### Phase 2: Refinement (Week 3-4)
- Improve based on feedback
- Add missing intents
- Enhance response quality
- A/B test form vs chat

### Phase 3: Default (Week 5+)
- Make chat the default
- Keep form UI as "Classic Mode"
- Full feature parity
- Production monitoring

---

## 12. Success Metrics

### Quantitative
- **Engagement**: Messages per session
- **Completion**: % searches that lead to bookings
- **Speed**: Time from start to booking
- **Satisfaction**: User ratings
- **Adoption**: % users using chat vs form

### Qualitative
- User feedback surveys
- Support ticket reduction
- Feature requests
- User testimonials

---

## 13. Technology Recommendations

### MVP (Recommended for Quick Start)

```
Frontend:
- Vanilla JavaScript (or Alpine.js for reactivity)
- CSS animations for smooth UX
- Existing Bootstrap for consistency

Backend:
- Flask route: /api/chat
- Rule-based intent router
- Session-based context storage
- Reuse all existing functions

No AI/LLM needed:
- Pattern matching for intents
- Template-based responses
- Works offline, no API costs
```

### Advanced (For Best Experience)

```
Frontend:
- React or Vue for rich UI
- WebSocket for real-time
- Progressive Web App

Backend:
- Claude API for NLU
- Redis for session state
- Async processing (Celery)

Infrastructure:
- Load balancer
- CDN for assets
- Monitoring (Sentry)
```

---

## 14. Example Prompts to Handle

The system should handle these types of requests:

**Search Intents:**
- "Find me a court tomorrow at 6pm"
- "I want to play tennis next Monday evening"
- "Show available courts this weekend"
- "Any courts free right now?"
- "Search for trainer Tobias on Friday"

**Booking Intents:**
- "Book it"
- "I'll take option 2"
- "Reserve the first one"
- "Yes, book that court"
- "Book Platz 5 tomorrow at 18:00"

**Information Intents:**
- "What are my bookings?"
- "Show my history"
- "Do I have anything booked for next week?"
- "When did I last play?"
- "What trainers are available?"

**Modification Intents:**
- "Actually, make it 7pm instead"
- "Show me Post SV instead"
- "Only trainers, not courts"
- "Different day"
- "Show more results"

**Casual Conversation:**
- "Thanks!"
- "Never mind"
- "Help"
- "What can you do?"
- "Hi"

---

## 15. Sample Implementation Pseudocode

```python
# /api/chat endpoint
@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    user_message = request.json['message']
    session_id = request.json.get('session_id')

    # Get or create session
    context = get_session_context(session_id)

    # Understand intent
    intent, entities = parse_intent(user_message, context)

    # Route to action
    if intent == 'search_court':
        results = search_courts(
            date=entities['date'],
            time=entities['time'],
            locations=entities.get('locations', ['arsenal', 'postsv'])
        )
        context['last_results'] = results
        context['state'] = 'RESULTS_SHOWN'
        reply = format_search_results(results, 'court')

    elif intent == 'book':
        slot_ref = entities.get('slot_reference')  # "option 1", "first one"
        slot = resolve_slot_reference(slot_ref, context['last_results'])

        success, message = book_court(slot)
        if success:
            context['state'] = 'BOOKING_CONFIRMED'
            reply = f"✓ Booked! {message} See you on court! 🎾"
        else:
            reply = f"Oops! {message}. Try a different slot?"

    elif intent == 'history':
        bookings = get_user_bookings(current_user.id)
        reply = format_booking_history(bookings)

    else:
        reply = "I'm not sure what you mean. Try 'find court tomorrow 6pm'"

    # Save context
    save_session_context(session_id, context)

    return jsonify({
        'reply': reply,
        'suggestions': generate_suggestions(intent, context),
        'session_id': session_id
    })


def parse_intent(message, context):
    """Simple rule-based intent parser"""
    msg_lower = message.lower()

    # Intents
    if any(word in msg_lower for word in ['find', 'search', 'show', 'available']):
        intent = 'search_court' if 'trainer' not in msg_lower else 'search_trainer'
    elif any(word in msg_lower for word in ['book', 'reserve', 'take']):
        intent = 'book'
    elif any(word in msg_lower for word in ['history', 'bookings', 'booked']):
        intent = 'history'
    else:
        intent = 'unknown'

    # Extract entities
    entities = {
        'date': extract_date(message),  # Use timeframe_parser
        'time': extract_time(message),
        'location': extract_location(message),
        'trainer_name': extract_trainer_name(message),
        'slot_reference': extract_slot_reference(message, context)
    }

    return intent, entities
```

---

## 16. Conclusion

A conversational interface for the Tennis Booking app would provide a more natural, engaging, and efficient user experience. By leveraging existing functionality and wrapping it in a chat-based interface, we can create a ChatGPT-like experience focused solely on tennis bookings.

### Recommended Next Steps:

1. **Validate the concept** with users (show mockups, gather feedback)
2. **Build MVP (Phase 1)** - Simple chat UI with rule-based routing (2-3 days)
3. **Test and iterate** - Collect real usage data
4. **Enhance gradually** - Add better NLU, LLM integration as needed
5. **Make it default** - Replace form UI once proven

### Key Success Factors:

- Keep it simple initially (rule-based, no AI needed)
- Reuse ALL existing backend code
- Focus on core flows (search, book)
- Provide fallbacks (quick actions, buttons)
- Measure and iterate based on real usage

The beauty of this approach is that we can start simple and enhance progressively, always keeping the existing form UI as a fallback. Users get choice, and we get valuable data on what works better.

---

**End of Concept Document**
