class InvalidTicketQuantityError(Exception):
    """Custom exception raised when ticket quantity is invalid."""
    pass


# Event data (event_number: {"name": event_name, "tickets": available_tickets})
events = {
    1: {"name": "Movie: Inception", "tickets": 50},
    2: {"name": "Concert: Coldplay", "tickets": 75},
    3: {"name": "Play: Hamlet", "tickets": 40}
}


def display_events():
    print("\nAvailable Events:")
    for number, details in events.items():
        print(f"{number}. {details['name']} (Tickets Available: {details['tickets']})")


def get_event_choice():
    try:
        choice = int(input("\nEnter the number of the event you want to book: "))

        if choice in events:
            return choice
        else:
            print("Error: Please select a valid event number (1-3).")
            return None

    except ValueError:
        print("Error: Event selection must be a number.")
        return None


def get_ticket_quantity(event_choice):
    try:
        quantity = int(input("Enter number of tickets to book: "))

        if quantity <= 0:
            raise InvalidTicketQuantityError(
                "Custom Error: Ticket quantity must be greater than 0."
            )

        elif quantity > events[event_choice]["tickets"]:
            raise InvalidTicketQuantityError(
                "Custom Error: Not enough tickets available for this event."
            )

        else:
            return quantity

    except ValueError:
        print("Error: Please enter a valid whole number for tickets.")
        return None

    except InvalidTicketQuantityError as e:
        print(e)
        return None


def book_tickets():
    display_events()

    event_choice = get_event_choice()
    if event_choice is None:
        return

    quantity = get_ticket_quantity(event_choice)
    if quantity is None:
        return

    # Deduct booked tickets
    events[event_choice]["tickets"] -= quantity

    print(f"\nSuccess! You booked {quantity} ticket(s) for {events[event_choice]['name']}.")
    print(f"Remaining tickets: {events[event_choice]['tickets']}")


def main():
    print("=== Online Ticket Booking System ===")
    book_tickets()


if __name__ == "__main__":
    main()
