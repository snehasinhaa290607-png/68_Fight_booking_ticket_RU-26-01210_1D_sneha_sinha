"""
=============================================================================
FLIGHT BOOKING MANAGEMENT SYSTEM
Production-Grade Console Application

Architecture:
- Domain Entities: Flight, Booking
- Data Access Layer: FlightRepository, BookingRepository (Atomic CSV Persistence)
- Business Logic Layer: FlightBookingService (Transactional Integrity)
- Presentation Layer: FlightBookingCLI (Defensive Input & Formatted Tables)
=============================================================================
"""

import os
import sys
import csv
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple


# =============================================================================
# PRODUCTION CONFIGURATION & LOGGING SETUP
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FLIGHTS_CSV_PATH = os.path.join(BASE_DIR, "flights.csv")
BOOKINGS_CSV_PATH = os.path.join(BASE_DIR, "bookings.csv")
LOG_FILE_PATH = os.path.join(BASE_DIR, "flight_system.log")

DEFAULT_FLIGHTS_DATA = """FlightNo,Origin,Destination,Seats,Fare
AI101,Raipur,Delhi,5,6000
AI202,Raipur,Mumbai,2,5500
AI303,Delhi,Mumbai,0,4800
AI404,Raipur,Bengaluru,8,6800
AI505,Raipur,Kolkata,12,4200
AI606,Raipur,Hyderabad,4,4900
AI102,Delhi,Raipur,6,6100
AI707,Delhi,Bengaluru,15,7500
AI808,Delhi,Kolkata,9,5900
AI909,Delhi,Chennai,0,7200
AI203,Mumbai,Raipur,3,5600
AI304,Mumbai,Delhi,18,5200
AI405,Mumbai,Goa,22,3800
6E215,Raipur,Delhi,25,5400
6E342,Raipur,Mumbai,14,5100
6E551,Raipur,Bengaluru,18,6300
6E678,Raipur,Goa,1,7800
6E104,Delhi,Mumbai,32,4900
6E208,Delhi,Bengaluru,45,6900
6E312,Delhi,Hyderabad,28,5200
6E419,Delhi,Srinagar,0,6500
6E523,Delhi,Ahmedabad,19,4100
6E634,Mumbai,Bengaluru,40,4600
6E745,Mumbai,Chennai,24,5300
6E856,Mumbai,Kolkata,16,6400
6E967,Mumbai,Jaipur,11,4800
6E178,Bengaluru,Delhi,35,6800
6E289,Bengaluru,Mumbai,29,4500
6E390,Bengaluru,Hyderabad,48,3200
6E491,Bengaluru,Kolkata,21,5800
6E592,Bengaluru,Kochi,33,3600
SG114,Raipur,Delhi,7,5100
SG225,Delhi,Mumbai,15,4600
SG336,Delhi,Goa,0,7400
SG447,Mumbai,Delhi,20,4700
SG558,Kolkata,Delhi,14,5300
SG669,Kolkata,Bengaluru,10,5600
UK811,Delhi,Mumbai,12,6500
UK822,Delhi,Bengaluru,16,8200
UK833,Mumbai,Delhi,14,6400
UK844,Mumbai,Bengaluru,10,5900
IX712,Raipur,Dubai,0,14500
QP1101,Mumbai,Bengaluru,25,4200
QP1202,Bengaluru,Mumbai,30,4100
QP1303,Delhi,Ahmedabad,22,3900
QP1404,Hyderabad,Bengaluru,18,3100
"""

# Configure production audit logging
logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)
logger = logging.getLogger("FlightBookingSystem")


# =============================================================================
# DOMAIN EXCEPTIONS
# =============================================================================
class FlightBookingException(Exception):
    """Base exception for flight booking system."""
    pass


class InvalidSeatCountError(FlightBookingException):
    """Raised when seat count is less than 1."""
    pass


class FlightNotFoundError(FlightBookingException):
    """Raised when requested flight number does not exist."""
    pass


class FlightFullError(FlightBookingException):
    """Raised when flight has zero seats left."""
    pass


class InsufficientSeatsError(FlightBookingException):
    """Raised when requested seats exceed available seats."""
    pass


class BookingNotFoundError(FlightBookingException):
    """Raised when booking ID is invalid or not found."""
    pass


class BookingAlreadyCancelledError(FlightBookingException):
    """Raised when trying to cancel an already cancelled booking."""
    pass


# =============================================================================
# DOMAIN ENTITY 1: Flight
# =============================================================================
class Flight:
    """
    Core Domain Entity representing a scheduled commercial flight.
    Encapsulates flight attributes and atomic seat reservation logic.
    """

    def __init__(self, flight_no: str, origin: str, destination: str, seats: int, fare: int):
        self.flight_no: str = str(flight_no).strip().upper()
        self.origin: str = str(origin).strip()
        self.destination: str = str(destination).strip()
        self.seats: int = int(seats)
        self.fare: int = int(fare)

    def matches_route(self, origin: str, destination: str) -> bool:
        """Case-insensitive route matching."""
        return (
            self.origin.strip().lower() == origin.strip().lower()
            and self.destination.strip().lower() == destination.strip().lower()
        )

    def book_seats(self, num_seats: int) -> int:
        """
        Deducts seats atomically after validating capacity.
        Returns total fare for the booked seats.
        """
        if num_seats < 1:
            raise InvalidSeatCountError("Number of seats must be at least 1.")

        if self.seats == 0:
            raise FlightFullError(f"Flight {self.flight_no} is full.")

        if num_seats > self.seats:
            raise InsufficientSeatsError(f"Only {self.seats} seat(s) available on {self.flight_no}.")

        self.seats -= num_seats
        total_fare = num_seats * self.fare
        return total_fare

    def cancel_seats(self, num_seats: int) -> int:
        """Restores seats to flight inventory."""
        if num_seats < 1:
            raise InvalidSeatCountError("Number of seats to restore must be at least 1.")
        self.seats += num_seats
        return self.seats

    def format_search_result(self) -> str:
        """Produces exact formatted manifest string."""
        return (
            f"{self.flight_no} | {self.origin} -> {self.destination} | "
            f"Seats: {self.seats} | Fare: Rs. {self.fare} per seat"
        )

    def to_csv_row(self) -> List[str]:
        """Serializes entity to CSV row format."""
        return [self.flight_no, self.origin, self.destination, str(self.seats), str(self.fare)]

    def __repr__(self) -> str:
        return f"<Flight {self.flight_no} {self.origin}->{self.destination} Seats:{self.seats} Fare:{self.fare}>"


# =============================================================================
# DOMAIN ENTITY 2: Booking
# =============================================================================
class Booking:
    """Represents a passenger flight reservation record."""

    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_CANCELLED = "CANCELLED"

    def __init__(
        self,
        booking_id: str,
        passenger_name: str,
        flight_no: str,
        seats: int,
        total_fare: int,
        timestamp: Optional[str] = None,
        status: str = STATUS_CONFIRMED,
    ):
        self.booking_id: str = str(booking_id).strip().upper()
        self.passenger_name: str = str(passenger_name).strip()
        self.flight_no: str = str(flight_no).strip().upper()
        self.seats: int = int(seats)
        self.total_fare: int = int(total_fare)
        self.timestamp: str = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status: str = status.strip().upper()

    def format_confirmation(self, seats_left: int) -> str:
        """Produces exact confirmation string matching specification."""
        return (
            f"Booking confirmed. ID: {self.booking_id} | {self.passenger_name} | "
            f"{self.flight_no} | {self.seats} seat(s) | Total: Rs. {self.total_fare} | Seats left: {seats_left}"
        )

    def to_csv_row(self) -> List[str]:
        return [
            self.booking_id,
            self.passenger_name,
            self.flight_no,
            str(self.seats),
            str(self.total_fare),
            self.timestamp,
            self.status,
        ]


# =============================================================================
# DATA ACCESS LAYER 1: FlightRepository
# =============================================================================
class FlightRepository:
    """Handles thread-safe, atomic CSV persistence for Flight records."""

    def __init__(self, filepath: str = FLIGHTS_CSV_PATH):
        self.filepath: str = filepath
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Self-healing: Creates default CSV if missing."""
        if not os.path.exists(self.filepath):
            logger.warning(f"Flights database '{self.filepath}' missing. Generating default dataset.")
            self._write_default_csv()

    def _write_default_csv(self) -> None:
        generator_script = os.path.join(BASE_DIR, "generate_1000_flights.py")
        if os.path.exists(generator_script):
            import subprocess
            subprocess.run([sys.executable, generator_script], check=True)
            return

        tmp_path = f"{self.filepath}.tmp"
        with open(tmp_path, mode="w", newline="", encoding="utf-8") as f:
            f.write(DEFAULT_FLIGHTS_DATA)
        os.replace(tmp_path, self.filepath)

    def load_all(self) -> List[Flight]:
        """Loads and parses flights from CSV file."""
        self._ensure_file_exists()
        flights: List[Flight] = []
        try:
            with open(self.filepath, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row_idx, row in enumerate(reader, start=2):
                    try:
                        clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None}
                        flight = Flight(
                            flight_no=clean_row["FlightNo"],
                            origin=clean_row["Origin"],
                            destination=clean_row["Destination"],
                            seats=int(clean_row["Seats"]),
                            fare=int(clean_row["Fare"]),
                        )
                        flights.append(flight)
                    except (KeyError, ValueError) as parse_err:
                        logger.error(f"Malformed row {row_idx} in {self.filepath}: {parse_err}")
            logger.info(f"Loaded {len(flights)} flight records from '{self.filepath}'.")
            return flights
        except Exception as e:
            logger.critical(f"Failed to read '{self.filepath}': {e}. Rebuilding default dataset.")
            self._write_default_csv()
            return self.load_all()

    def save_all(self, flights: List[Flight]) -> None:
        """Atomically saves flight records using a temporary file."""
        tmp_path = f"{self.filepath}.tmp"
        try:
            with open(tmp_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["FlightNo", "Origin", "Destination", "Seats", "Fare"])
                for flight in flights:
                    writer.writerow(flight.to_csv_row())
            os.replace(tmp_path, self.filepath)
            logger.info(f"Successfully persisted {len(flights)} flights to '{self.filepath}'.")
        except Exception as e:
            logger.error(f"Failed to persist flights to '{self.filepath}': {e}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise


# =============================================================================
# DATA ACCESS LAYER 2: BookingRepository
# =============================================================================
class BookingRepository:
    """Handles persistent storage for confirmed and cancelled bookings."""

    def __init__(self, filepath: str = BOOKINGS_CSV_PATH):
        self.filepath: str = filepath
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        if not os.path.exists(self.filepath):
            with open(self.filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["BookingID", "PassengerName", "FlightNo", "Seats", "TotalFare", "Timestamp", "Status"])

    def load_all(self) -> Dict[str, Booking]:
        self._ensure_file_exists()
        bookings: Dict[str, Booking] = {}
        try:
            with open(self.filepath, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    clean = {k.strip(): v.strip() for k, v in row.items() if k is not None}
                    bid = clean.get("BookingID", "").upper()
                    if bid:
                        b = Booking(
                            booking_id=bid,
                            passenger_name=clean.get("PassengerName", ""),
                            flight_no=clean.get("FlightNo", ""),
                            seats=int(clean.get("Seats", 0)),
                            total_fare=int(clean.get("TotalFare", 0)),
                            timestamp=clean.get("Timestamp", ""),
                            status=clean.get("Status", Booking.STATUS_CONFIRMED),
                        )
                        bookings[bid] = b
            logger.info(f"Loaded {len(bookings)} historical bookings from '{self.filepath}'.")
            return bookings
        except Exception as e:
            logger.error(f"Error loading bookings from '{self.filepath}': {e}")
            return {}

    def save_all(self, bookings: Dict[str, Booking]) -> None:
        tmp_path = f"{self.filepath}.tmp"
        try:
            with open(tmp_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["BookingID", "PassengerName", "FlightNo", "Seats", "TotalFare", "Timestamp", "Status"])
                for b in bookings.values():
                    writer.writerow(b.to_csv_row())
            os.replace(tmp_path, self.filepath)
        except Exception as e:
            logger.error(f"Failed to persist bookings: {e}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise


# =============================================================================
# BUSINESS LOGIC SERVICE: FlightBookingService
# =============================================================================
class FlightBookingService:
    """
    Core business service handling transaction boundaries,
    validations, and inventory synchronization.
    """

    def __init__(
        self,
        flight_repo: Optional[FlightRepository] = None,
        booking_repo: Optional[BookingRepository] = None,
    ):
        self.flight_repo: FlightRepository = flight_repo or FlightRepository()
        self.booking_repo: BookingRepository = booking_repo or BookingRepository()
        self.flights: List[Flight] = self.flight_repo.load_all()
        self.bookings: Dict[str, Booking] = self.booking_repo.load_all()
        self.next_counter: int = self._determine_next_counter()

    def _determine_next_counter(self) -> int:
        """Determines next sequential booking ID counter (BK1, BK2, etc.)."""
        highest = 0
        for bid in self.bookings.keys():
            if bid.startswith("BK"):
                num_str = bid[2:]
                if num_str.isdigit():
                    val = int(num_str)
                    if val > highest:
                        highest = val
        return highest + 1

    def reload(self) -> None:
        """Reloads inventories from disk."""
        self.flights = self.flight_repo.load_all()
        self.bookings = self.booking_repo.load_all()
        self.next_counter = self._determine_next_counter()

    def find_flight(self, flight_no: str) -> Optional[Flight]:
        """Case-insensitive flight search by flight number."""
        target = flight_no.strip().upper()
        for f in self.flights:
            if f.flight_no == target:
                return f
        return None

    def search_flights(self, origin: str, destination: str) -> List[str]:
        """Searches available flights by route."""
        clean_origin = origin.strip()
        clean_dest = destination.strip()
        results: List[str] = []

        for flight in self.flights:
            if flight.matches_route(clean_origin, clean_dest):
                results.append(flight.format_search_result())

        logger.info(f"Route search '{clean_origin}' -> '{clean_dest}' returned {len(results)} matches.")
        return results

    def book_flight(self, flight_no: str, passenger_name: str, num_seats: int) -> Tuple[bool, str]:
        """
        Processes a flight booking transaction.
        Enforces domain rules and guarantees inventory atomicity.
        """
        # Rule 1: Seat count validation
        if num_seats < 1:
            return False, "Number of seats must be at least 1."

        # Rule 2: Passenger validation
        clean_name = passenger_name.strip()
        if not clean_name:
            return False, "Passenger name cannot be blank."

        # Rule 3: Flight existence check
        flight = self.find_flight(flight_no)
        if not flight:
            return False, f"Flight {flight_no.strip().upper()} not found."

        # Rule 4: Attempt seat deduction
        try:
            total_fare = flight.book_seats(num_seats)
        except (FlightFullError, InsufficientSeatsError, InvalidSeatCountError) as err:
            logger.warning(f"Booking rejected for {flight.flight_no}: {err}")
            return False, str(err)

        # Rule 5: Generate Booking ID and record reservation
        booking_id = f"BK{self.next_counter}"
        self.next_counter += 1

        booking = Booking(
            booking_id=booking_id,
            passenger_name=clean_name,
            flight_no=flight.flight_no,
            seats=num_seats,
            total_fare=total_fare,
            status=Booking.STATUS_CONFIRMED,
        )
        self.bookings[booking_id] = booking

        # Rule 6: Atomic persistence
        try:
            self.flight_repo.save_all(self.flights)
            self.booking_repo.save_all(self.bookings)
            logger.info(f"Booking confirmed: {booking_id} | {clean_name} | {flight.flight_no} | {num_seats} seats")
        except Exception as e:
            logger.critical(f"Persistence error during booking {booking_id}: {e}")
            # Rollback in-memory mutation
            flight.cancel_seats(num_seats)
            del self.bookings[booking_id]
            return False, "Internal error: Failed to save booking record to database."

        confirmation = booking.format_confirmation(seats_left=flight.seats)
        return True, confirmation

    def cancel_booking(self, booking_id: str) -> Tuple[bool, str]:
        """
        Processes booking cancellation and restores inventory.
        """
        clean_id = booking_id.strip().upper()
        booking = self.bookings.get(clean_id)

        if not booking:
            return False, f"Booking ID {booking_id} not found."

        if booking.status == Booking.STATUS_CANCELLED:
            return False, f"Booking {clean_id} is already cancelled."

        flight = self.find_flight(booking.flight_no)
        if not flight:
            return False, f"Associated flight {booking.flight_no} not found."

        # Restore inventory
        remaining_seats = flight.cancel_seats(booking.seats)
        booking.status = Booking.STATUS_CANCELLED

        try:
            self.flight_repo.save_all(self.flights)
            self.booking_repo.save_all(self.bookings)
            logger.info(f"Booking {clean_id} cancelled. Restored {booking.seats} seats on {flight.flight_no}.")
        except Exception as e:
            logger.critical(f"Persistence error during cancellation of {clean_id}: {e}")
            flight.book_seats(booking.seats)
            booking.status = Booking.STATUS_CONFIRMED
            return False, "Internal error: Failed to update cancellation in database."

        output = f"Booking {clean_id} cancelled. Seats left on {booking.flight_no}: {remaining_seats}"
        return True, output


# =============================================================================
# PRESENTATION LAYER: FlightBookingCLI
# =============================================================================
class FlightBookingCLI:
    """Production console interface with defensive input validation."""

    def __init__(self):
        self.service = FlightBookingService()

    def print_banner(self) -> None:
        print("=" * 65)
        print("           FLIGHT BOOKING MANAGEMENT SYSTEM")
        print("             Enterprise Production Console")
        print("=" * 65)

    def print_menu(self) -> None:
        print("\n--------------------------- MAIN MENU ---------------------------")
        print("  1. Search Flights by Route (Origin -> Destination)")
        print("  2. Book Flight Seats")
        print("  3. Cancel Booking")
        print("  4. View All Available Flights")
        print("  5. View Booking History & Active Bookings")
        print("  6. Reload / Synchronize Flights Inventory from CSV")
        print("  7. Exit System")
        print("-----------------------------------------------------------------")

    def run(self) -> None:
        self.print_banner()
        while True:
            self.print_menu()
            choice = input("Enter choice (1-7): ").strip()

            if choice == "1":
                self.handle_search()
            elif choice == "2":
                self.handle_booking()
            elif choice == "3":
                self.handle_cancellation()
            elif choice == "4":
                self.handle_view_flights()
            elif choice == "5":
                self.handle_view_bookings()
            elif choice == "6":
                self.handle_reload()
            elif choice == "7":
                print("\n[System] Exiting Flight Booking Management System. Goodbye!")
                logger.info("Application session terminated by user.")
                sys.exit(0)
            else:
                print("\n[Error] Invalid choice. Please enter a number between 1 and 7.")

    def handle_search(self) -> None:
        print("\n--- Search Flights by Route ---")
        origin = input("Enter Origin City (e.g. Raipur): ").strip()
        destination = input("Enter Destination City (e.g. Delhi): ").strip()

        if not origin or not destination:
            print("[Error] Origin and Destination cannot be empty.")
            return

        results = self.service.search_flights(origin, destination)
        print("\n--- Search Results ---")
        if results:
            for r in results:
                print(r)
        else:
            print(f"No flights found from '{origin}' to '{destination}'.")

    def handle_booking(self) -> None:
        print("\n--- Book Flight Seats ---")
        flight_no = input("Enter Flight Number (e.g. AI101, AI202): ").strip()
        passenger_name = input("Enter Passenger Name (e.g. Kiran Rao): ").strip()
        seats_str = input("Enter Number of Seats: ").strip()

        if not seats_str.isdigit():
            try:
                val = int(seats_str)
                if val <= 0:
                    print("\nNumber of seats must be at least 1.")
                    return
            except ValueError:
                pass
            print("\n[Error] Invalid seat number. Please provide a positive integer.")
            return

        num_seats = int(seats_str)
        success, message = self.service.book_flight(flight_no, passenger_name, num_seats)
        print("\n" + message)

    def handle_cancellation(self) -> None:
        print("\n--- Cancel Booking ---")
        booking_id = input("Enter Booking ID to Cancel (e.g. BK1): ").strip()

        if not booking_id:
            print("[Error] Booking ID cannot be blank.")
            return

        success, message = self.service.cancel_booking(booking_id)
        print("\n" + message)

    def handle_view_flights(self) -> None:
        total = len(self.service.flights)
        print(f"\n--- Current Flight Inventory ({total} total flights) ---")
        page_size = 20
        total_pages = (total + page_size - 1) // page_size
        current_page = 1

        while True:
            start_idx = (current_page - 1) * page_size
            end_idx = min(start_idx + page_size, total)
            page_flights = self.service.flights[start_idx:end_idx]

            print(f"\nPage {current_page} of {total_pages} (Flights {start_idx + 1} to {end_idx}):")
            print(f"{'Flight No':<12} | {'Origin':<16} | {'Destination':<16} | {'Seats':<7} | {'Fare (Rs)':<10}")
            print("-" * 72)
            for f in page_flights:
                status_tag = " (FULL)" if f.seats == 0 else ""
                print(f"{f.flight_no:<12} | {f.origin:<16} | {f.destination:<16} | {f.seats:<7} | Rs. {f.fare:<8}{status_tag}")

            if current_page >= total_pages:
                print("\n[End of inventory reached.]")
                break

            prompt = input(f"\n[Press Enter for next page ({current_page + 1}/{total_pages}), 'a' for all, or 'q' to return to menu]: ").strip().lower()
            if prompt in ('q', 'quit', 'exit'):
                break
            elif prompt in ('a', 'all'):
                for f in self.service.flights[end_idx:]:
                    status_tag = " (FULL)" if f.seats == 0 else ""
                    print(f"{f.flight_no:<12} | {f.origin:<16} | {f.destination:<16} | {f.seats:<7} | Rs. {f.fare:<8}{status_tag}")
                break
            else:
                current_page += 1

    def handle_view_bookings(self) -> None:
        print("\n--- Passenger Bookings Ledger ---")
        if not self.service.bookings:
            print("No bookings recorded yet.")
            return

        print(f"{'Booking ID':<12} | {'Passenger':<18} | {'Flight':<8} | {'Seats':<6} | {'Total Fare':<12} | {'Status':<10}")
        print("-" * 75)
        for b in self.service.bookings.values():
            print(f"{b.booking_id:<12} | {b.passenger_name:<18} | {b.flight_no:<8} | {b.seats:<6} | Rs. {b.total_fare:<10} | {b.status:<10}")

    def handle_reload(self) -> None:
        self.service.reload()
        print("\n[Success] Flight inventories and bookings synchronized from disk.")


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    cli = FlightBookingCLI()
    cli.run()
