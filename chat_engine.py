"""Conversational interface engine for Tennis Booking app."""

import re
from datetime import datetime
from timeframe_parser import TimeframeParser
from scrapers_v2 import scrape_all_portals
from trainer_finder import find_trainers
from booking import book_court
from preference_engine import PreferenceEngine


class ChatEngine:
    """Handles conversational interactions for tennis booking."""

    def __init__(self):
        self.timeframe_parser = TimeframeParser()
        self.pref_engine = PreferenceEngine()

    def parse_intent(self, message, context):
        """Parse user message to determine intent and extract entities.

        Args:
            message: User's message text
            context: Current conversation context

        Returns:
            (intent, entities) tuple
        """
        msg_lower = message.lower().strip()

        # Detect intent
        intent = 'unknown'

        # Greeting
        if any(word in msg_lower for word in ['hi', 'hello', 'hey', 'start']):
            intent = 'greeting'

        # Search intents
        elif any(word in msg_lower for word in ['find', 'search', 'show', 'available', 'look for', 'i want', 'need']):
            if 'trainer' in msg_lower:
                intent = 'search_trainer'
            else:
                intent = 'search_court'

        # Booking intents
        elif any(word in msg_lower for word in ['book', 'reserve', 'take', "i'll take"]):
            intent = 'book'

        # History/Info
        elif any(word in msg_lower for word in ['history', 'bookings', 'booked', 'my bookings', 'what did i']):
            intent = 'history'

        # Help
        elif any(word in msg_lower for word in ['help', 'what can you', 'how do']):
            intent = 'help'

        # Thanks
        elif any(word in msg_lower for word in ['thanks', 'thank you', 'great', 'perfect']):
            intent = 'thanks'

        # Cancel
        elif any(word in msg_lower for word in ['cancel', 'never mind', 'nevermind', 'stop']):
            intent = 'cancel'

        # Extract entities
        entities = {
            'trainer_name': self._extract_trainer_name(msg_lower),
            'location': self._extract_location(msg_lower),
            'slot_reference': self._extract_slot_reference(msg_lower, context)
        }

        # Extract date/time using existing parser if relevant
        if intent in ['search_court', 'search_trainer']:
            try:
                parsed = self.timeframe_parser.parse(message)
                entities['date'] = parsed.get('date')
                entities['start_time'] = parsed.get('start_time')
                entities['end_time'] = parsed.get('end_time')
            except:
                entities['date'] = None
                entities['start_time'] = None
                entities['end_time'] = None

        return intent, entities

    def _extract_trainer_name(self, message):
        """Extract trainer name from message."""
        trainers = ['tobias', 'rossen', 'tobias w', 'tobias w.']
        for trainer in trainers:
            if trainer in message:
                return trainer.title()
        return None

    def _extract_location(self, message):
        """Extract location preference from message."""
        locations = {'arsenal': False, 'postsv': False}

        if 'arsenal' in message or 'das spiel' in message:
            locations['arsenal'] = True
        if 'post sv' in message or 'postsv' in message:
            locations['postsv'] = True

        # Default: both if none specified
        if not locations['arsenal'] and not locations['postsv']:
            locations['arsenal'] = True
            locations['postsv'] = True

        return locations

    def _extract_slot_reference(self, message, context):
        """Extract reference to a slot from previous results."""
        # Look for patterns like "option 1", "first one", "number 2", etc.
        patterns = [
            r'option\s+(\d+)',
            r'number\s+(\d+)',
            r'slot\s+(\d+)',
            r'#(\d+)',
            r'^(\d+)$'
        ]

        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return int(match.group(1)) - 1  # Convert to 0-indexed

        # Handle words
        if 'first' in message or 'top' in message:
            return 0
        elif 'second' in message:
            return 1
        elif 'third' in message:
            return 2

        return None

    def process_message(self, message, context):
        """Process user message and generate response.

        Args:
            message: User's message
            context: Current conversation context

        Returns:
            Dictionary with reply, action, results, and updated context
        """
        intent, entities = self.parse_intent(message, context)

        response = {
            'reply': '',
            'action': None,
            'results': [],
            'suggestions': [],
            'context': context.copy()
        }

        # Route to appropriate handler
        if intent == 'greeting':
            response['reply'] = self._handle_greeting(context)
            response['suggestions'] = ['Find a court', 'Find a trainer', 'Show my bookings']

        elif intent == 'search_court':
            return self._handle_search_court(entities, context)

        elif intent == 'search_trainer':
            return self._handle_search_trainer(entities, context)

        elif intent == 'book':
            return self._handle_booking(entities, context)

        elif intent == 'history':
            response['reply'] = "Looking at your booking history...\n\nBooking history feature coming soon! For now, you can search for courts and book them directly."
            response['suggestions'] = ['Find a court', 'Find a trainer']

        elif intent == 'help':
            response['reply'] = self._handle_help()
            response['suggestions'] = ['Find court tomorrow 6pm', 'Show trainers', 'Find a court']

        elif intent == 'thanks':
            response['reply'] = "You're welcome! Anything else I can help you with? 🎾"
            response['suggestions'] = ['Find another court', 'Show my bookings']

        elif intent == 'cancel':
            response['reply'] = "No problem! Let me know if you need anything else."
            response['context']['state'] = 'IDLE'
            response['context']['last_results'] = []
            response['suggestions'] = ['Find a court', 'Find a trainer']

        else:
            response['reply'] = self._handle_unknown(message, context)
            response['suggestions'] = ['Find court tomorrow 6pm', 'Find trainer', 'Help']

        return response

    def _handle_greeting(self, context):
        """Handle greeting messages."""
        return ("Hi! I'm your tennis booking assistant. 🎾\n\n"
                "I can help you:\n"
                "• Find available tennis courts at Arsenal and Post SV\n"
                "• Search for trainers at Arsenal\n"
                "• Book courts and trainer sessions\n\n"
                "Just tell me what you'd like to do! For example:\n"
                "- 'Find a court tomorrow at 6pm'\n"
                "- 'I need a trainer next Monday morning'\n"
                "- 'Show available courts this weekend'")

    def _handle_help(self):
        """Handle help requests."""
        return ("Here's what you can ask me:\n\n"
                "**Search for courts:**\n"
                "• 'Find a court tomorrow at 18:00'\n"
                "• 'Show available courts next Monday evening'\n"
                "• 'I want to play tennis this Friday 6pm'\n\n"
                "**Search for trainers:**\n"
                "• 'Find a trainer tomorrow morning'\n"
                "• 'I need trainer Tobias on Friday'\n\n"
                "**Book:**\n"
                "• 'Book option 1'\n"
                "• 'I'll take the first one'\n"
                "• 'Reserve number 2'\n\n"
                "Just ask naturally and I'll understand! 🎾")

    def _handle_unknown(self, message, context):
        """Handle unknown intents."""
        return ("I'm not sure what you mean. Try asking me to:\n"
                "• Find a court (e.g., 'tomorrow at 6pm')\n"
                "• Find a trainer (e.g., 'next Monday morning')\n"
                "• Book a court (e.g., 'book option 1')\n\n"
                "Or just say 'help' to see examples!")

    def _handle_search_court(self, entities, context):
        """Handle court search requests."""
        date = entities.get('date')
        start_time = entities.get('start_time')
        end_time = entities.get('end_time')
        locations = entities.get('location', {'arsenal': True, 'postsv': True})

        # Check if we have required info
        if not date or not start_time:
            return {
                'reply': ("I'd be happy to search for courts! When would you like to play?\n\n"
                          "For example, you can say:\n"
                          "• 'tomorrow at 18:00'\n"
                          "• 'next Friday evening'\n"
                          "• '7.1.2026 between 15:00 and 18:00'"),
                'action': 'clarification_needed',
                'results': [],
                'suggestions': ['Tomorrow at 18:00', 'Next Monday 6pm', 'This weekend'],
                'context': context
            }

        # Search for courts
        try:
            slots = scrape_all_portals(date, start_time, end_time, locations)

            # Get preferred slot if available
            preferred_idx = None
            if self.pref_engine.has_confidence() and slots:
                preferred_slot = self.pref_engine.get_preferred_slot(slots)
                if preferred_slot:
                    try:
                        preferred_idx = slots.index(preferred_slot)
                    except ValueError:
                        preferred_idx = None

            # Format response
            if not slots:
                reply = (f"Sorry, I couldn't find any available courts for {date.strftime('%A, %B %d')} "
                        f"between {start_time} and {end_time}.\n\n"
                        "Would you like to try a different time or day?")
                suggestions = ['Different time', 'Tomorrow instead', 'This weekend']
            else:
                day_str = date.strftime('%A, %B %d')
                reply = f"Great! I found **{len(slots)} available courts** for {day_str}.\n\n"

                # Show top 3 results
                for i, slot in enumerate(slots[:3]):
                    prefix = "⭐ " if i == preferred_idx else f"{i+1}. "
                    venue = slot.get('venue', 'Unknown')
                    court = slot.get('court_name', 'Court')
                    time = slot.get('time', '')
                    price = slot.get('price', '')

                    reply += f"{prefix}**{court}** at {venue}\n"
                    reply += f"   {day_str} at {time}"
                    if price:
                        reply += f" (€{price})"
                    reply += "\n\n"

                if len(slots) > 3:
                    reply += f"_...and {len(slots) - 3} more options_\n\n"

                if preferred_idx is not None and preferred_idx < 3:
                    reply += "⭐ = Recommended based on your preferences\n\n"

                reply += "Which one would you like to book?"
                suggestions = ['Book option 1', 'Book option 2', 'Show more', 'Different time']

            # Update context
            new_context = context.copy()
            new_context['state'] = 'RESULTS_SHOWN' if slots else 'NO_RESULTS'
            new_context['last_search'] = {
                'type': 'court',
                'date': date.strftime('%Y-%m-%d'),
                'start_time': start_time,
                'end_time': end_time,
                'locations': locations
            }
            new_context['last_results'] = slots[:20]  # Store top 20

            return {
                'reply': reply,
                'action': 'search_results',
                'results': slots[:20],
                'suggestions': suggestions,
                'context': new_context
            }

        except Exception as e:
            return {
                'reply': f"Oops! Something went wrong while searching: {str(e)}\n\nPlease try again.",
                'action': 'error',
                'results': [],
                'suggestions': ['Try again', 'Find trainer instead'],
                'context': context
            }

    def _handle_search_trainer(self, entities, context):
        """Handle trainer search requests."""
        date = entities.get('date')
        start_time = entities.get('start_time')
        end_time = entities.get('end_time')
        trainer_name = entities.get('trainer_name')

        # Check if we have required info
        if not date or not start_time:
            return {
                'reply': ("I'd be happy to search for trainers! When would you like a training session?\n\n"
                          "For example:\n"
                          "• 'tomorrow morning'\n"
                          "• 'next Monday at 10:00'\n"
                          "• 'Friday afternoon'"),
                'action': 'clarification_needed',
                'results': [],
                'suggestions': ['Tomorrow morning', 'Next Monday 9am', 'This Friday'],
                'context': context
            }

        # Search for trainers
        try:
            trainers = find_trainers(date, start_time, end_time, trainer_name)

            # Format response
            if not trainers:
                reply = (f"Sorry, I couldn't find any available trainers for {date.strftime('%A, %B %d')} "
                        f"between {start_time} and {end_time}.\n\n"
                        "Would you like to try a different time?")
                suggestions = ['Different time', 'Find courts instead']
            else:
                day_str = date.strftime('%A, %B %d')
                if trainer_name:
                    reply = f"Good news! I found **{len(trainers)} sessions** with {trainer_name}:\n\n"
                else:
                    reply = f"Great! I found **{len(trainers)} available trainer sessions** for {day_str}:\n\n"

                # Show top 3 results
                for i, trainer in enumerate(trainers[:3]):
                    name = trainer.get('trainer_name', 'Trainer')
                    time_start = trainer.get('time_start', '')
                    time_end = trainer.get('time_end', '')
                    price = trainer.get('price', '')

                    reply += f"{i+1}. **{name}**\n"
                    reply += f"   {day_str}, {time_start}-{time_end}"
                    if price:
                        reply += f" (€{price})"
                    reply += "\n\n"

                if len(trainers) > 3:
                    reply += f"_...and {len(trainers) - 3} more sessions_\n\n"

                reply += "Which time works for you?"
                suggestions = ['Book option 1', 'Book option 2', 'Show more']

            # Update context
            new_context = context.copy()
            new_context['state'] = 'RESULTS_SHOWN' if trainers else 'NO_RESULTS'
            new_context['last_search'] = {
                'type': 'trainer',
                'date': date.strftime('%Y-%m-%d'),
                'start_time': start_time,
                'end_time': end_time,
                'trainer_name': trainer_name
            }
            new_context['last_results'] = trainers[:20]

            return {
                'reply': reply,
                'action': 'search_results',
                'results': trainers[:20],
                'suggestions': suggestions,
                'context': new_context
            }

        except Exception as e:
            return {
                'reply': f"Oops! Something went wrong while searching: {str(e)}\n\nPlease try again.",
                'action': 'error',
                'results': [],
                'suggestions': ['Try again', 'Find courts instead'],
                'context': context
            }

    def _handle_booking(self, entities, context):
        """Handle booking requests."""
        slot_ref = entities.get('slot_reference')
        last_results = context.get('last_results', [])

        # Check if we have results to book from
        if not last_results:
            return {
                'reply': ("I don't have any search results yet. Would you like me to search for courts or trainers first?\n\n"
                          "For example: 'Find a court tomorrow at 6pm'"),
                'action': 'error',
                'results': [],
                'suggestions': ['Find court tomorrow 6pm', 'Find trainer'],
                'context': context
            }

        # Check if we have a valid slot reference
        if slot_ref is None or slot_ref < 0 or slot_ref >= len(last_results):
            return {
                'reply': (f"Which option would you like to book? Please specify a number between 1 and {len(last_results)}.\n\n"
                          "For example: 'book option 1' or 'I'll take the first one'"),
                'action': 'clarification_needed',
                'results': [],
                'suggestions': ['Book option 1', 'Book option 2'],
                'context': context
            }

        # Get the selected slot
        slot = last_results[slot_ref]
        search_type = context.get('last_search', {}).get('type', 'court')

        # Book the slot
        try:
            if search_type == 'trainer':
                # For now, trainers can't be booked automatically
                return {
                    'reply': ("Trainer booking is not yet automated. Please contact Arsenal directly to book this session:\n\n"
                              f"**{slot.get('trainer_name')}**\n"
                              f"{slot.get('date')} at {slot.get('time_start')}-{slot.get('time_end')}\n\n"
                              "Would you like to search for something else?"),
                    'action': 'info',
                    'results': [],
                    'suggestions': ['Find a court', 'Different trainer'],
                    'context': context
                }
            else:
                # Book court
                success, message = book_court(slot)

                if success:
                    reply = f"✓ **Booked!** {message}\n\nSee you on court! 🎾\n\nAnything else I can help you with?"
                    suggestions = ['Find another court', 'Done']

                    # Update context
                    new_context = context.copy()
                    new_context['state'] = 'BOOKING_CONFIRMED'
                    new_context['last_booking'] = slot

                    return {
                        'reply': reply,
                        'action': 'booking_success',
                        'results': [slot],
                        'suggestions': suggestions,
                        'context': new_context
                    }
                else:
                    reply = f"❌ Oops! Booking failed: {message}\n\nWould you like to try a different slot?"
                    suggestions = ['Show more options', 'Try different time']

                    return {
                        'reply': reply,
                        'action': 'booking_failed',
                        'results': [],
                        'suggestions': suggestions,
                        'context': context
                    }

        except Exception as e:
            return {
                'reply': f"❌ Something went wrong: {str(e)}\n\nPlease try again or choose a different slot.",
                'action': 'error',
                'results': [],
                'suggestions': ['Try again', 'Different option'],
                'context': context
            }
