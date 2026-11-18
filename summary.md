# Academic Project Report: Flight Booking Management System

**Student Name:** Sneha Sinha  
**University Roll No:** RU-26-01210  
**Section:** 1D  
**Academic Year:** 2026-2027  
**Course:** Programming Fundamentals and Logic Building Using Python  
**Institution:** Rungta International Skills University, School of Computer Science & Engineering  
**Degree Program:** Bachelor of Technology in Computer Science and Engineering  
**Problem Statement Number:** 68 (PS No. 68)  
**Project Title:** Flight Booking Management System  
**Implementation Language:** Python 3  

---

## 1. Problem Formulation and Scope

Problem Statement No. 68 specifies:
> "Build a flight booking program using a class Flight. Load flights from flights.csv, search by origin and destination, book seats (total = seats x fare) and cancel bookings. Seat counts must always stay correct."

In commercial air travel and reservation software, maintaining seat count integrity across operations is critical. Overbooking or untracked cancellations directly corrupt inventory. This project implements a console-based flight reservation system in Python 3 that addresses these requirements through an object-oriented model and transactional CSV updates.

---

## 2. Requirements Compliance

| Parameter | Specification | Project Implementation |
| :--- | :--- | :--- |
| **Language & Delivery** | Python 3, single file execution from console | Implemented in `main.py` with an interactive command-line interface. Uses only the Python standard library. |
| **Object Model** | Class `Flight` with booking and cancellation logic | Class `Flight` encapsulates attributes (`flight_no`, `origin`, `destination`, `seats`, `fare`) and methods `book_seats()` and `cancel_seats()`. |
| **Persistence** | Load flights from `flights.csv` and handle missing files | `FlightRepository` reads `flights.csv` into a list of `Flight` objects. If the file is not found, default seed records are generated automatically. |
| **Search Function** | Search by origin and destination | Case-insensitive string matching allows queries such as `raipur` -> `delhi` to match `AI101`. |
| **Calculations** | Total fare = seats * fare | Verified dynamically during reservations (`seats * fare`) before seat deduction. |
| **Inventory Invariant** | Seat counts must remain accurate | Seats decrease on confirmed bookings and return to the exact previous count upon cancellation. |

---

## 3. System Design and Logic Flow

### 3.1 Layered OOP Structure
The application is organized into distinct layers inside `main.py`:

1. **Entity Layer (`Flight`, `Booking`)**:
   - `Flight`: Maintains core state attributes for each route. Provides `matches_route(origin, destination)`, `book_seats(num_seats)`, and `cancel_seats(num_seats)`.
   - `Booking`: Represents a confirmed ticket with a unique identifier (`BK1`, `BK2`, etc.), passenger name, flight number, reserved seats, total fare, and timestamp.

2. **Data Layer (`FlightRepository`, `BookingRepository`)**:
   - Handles CSV serialization and deserialization.
   - Uses atomic file writes (staging via `.tmp` followed by `os.replace`) to prevent file corruption during abrupt shutdowns.

3. **Service Layer (`FlightBookingService`)**:
   - Implements business logic and transaction boundaries.
   - Enforces validation checks: rejects non-positive seat requests, checks if a flight is full, prevents overbooking, and handles cancellations by ID.

4. **CLI Layer (`FlightBookingCLI`)**:
   - Manages user input, interactive prompts, formatted tabular outputs, and pagination.

### 3.2 Booking Logic Flow
```
[User Input: FlightNo, Name, Seats]
              |
     [Is Seats >= 1?] ---> No ---> [Error: Min 1 seat required]
              | Yes
    [Flight exists in DB?] ---> No ---> [Error: Flight not found]
              | Yes
    [Available Seats == 0?] ---> Yes ---> [Error: Flight is full]
              | No
[Requested > Available?] ---> Yes ---> [Error: Insufficient seats]
              | No
[Deduct Seats from Flight]
[Compute Total = Seats * Fare]
[Generate Booking ID (BKx)]
[Save Updated flights.csv atomically]
[Append Entry to bookings.csv]
[Return Success Message]
```

---

## 4. Dataset Overview (`flights.csv`)

The system operates on a database of 1,000 commercial flight schedules covering Indian metro routes and international sectors.

- **Columns:** `FlightNo`, `Origin`, `Destination`, `Seats`, `Fare`
- **Airlines Represented:** Air India, IndiGo, SpiceJet, Vistara, Akasa Air, Emirates, British Airways, Qatar Airways, Singapore Airlines
- **Seat Capacities:** 0 (sold out) to 180 seats per flight
- **Fare Range:** Rs. 2,400 to Rs. 45,000

The first three records represent the test benchmark routes:
```csv
FlightNo,Origin,Destination,Seats,Fare
AI101,Raipur,Delhi,5,6000
AI202,Raipur,Mumbai,2,5500
AI303,Delhi,Mumbai,0,4800
```

---

## 5. Verification Results and Terminal Proofs

### Test Case 1: Route Search (Normal Case)
- **Input:** Origin = `Raipur`, Destination = `Delhi`
- **Observed Output:**
  ```text
  AI101 | Raipur -> Delhi | Seats: 5 | Fare: Rs. 6000 per seat
  ```
- **Validation:** Exact match against assignment criteria.

![Test Case 1](test_case_1_screenshot.png)

---

### Test Case 2: Boundary Booking (Exhausting All Available Seats)
- **Input:** Flight = `AI202`, Passenger = `Kiran Rao`, Seats = `2` (Available: 2, Fare: 5500)
- **Observed Output:**
  ```text
  Booking confirmed. ID: BK1 | Kiran Rao | AI202 | 2 seat(s) | Total: Rs. 11000 | Seats left: 0
  ```
- **Validation:** $2 \times 5500 = 11000$ INR calculated correctly; remaining seats decremented to 0.

![Test Case 2](test_case_2_screenshot.png)

---

### Test Case 3: Rejection of Invalid Inputs and Overbooking
- **Scenario 3a (Flight Full):** Requesting 1 seat on `AI303` (0 available).
  - Output: `Flight AI303 is full.`
- **Scenario 3b (Exceeding Available Seats):** Requesting 6 seats on `AI101` (5 available).
  - Output: `Only 5 seat(s) available on AI101.`
- **Scenario 3c (Invalid Seat Count):** Requesting 0 seats.
  - Output: `Number of seats must be at least 1.`
- **Validation:** All invalid operations were caught and rejected without state modification.

![Test Case 3](test_case_3_screenshot.png)

---

### Test Case 4: Full Transaction Lifecycle (Booking Followed by Cancellation)
- **Step 1 (Booking):** Reserve 3 seats on `AI101` for `Priya Nair`.
  - Output: `Booking confirmed. ID: BK1 | Priya Nair | AI101 | 3 seat(s) | Total: Rs. 18000 | Seats left: 2`
- **Step 2 (Cancellation):** Cancel booking `BK1`.
  - Output: `Booking BK1 cancelled. Seats left on AI101: 5`
- **Validation:** Total seats on `AI101` returned to original inventory ($2 + 3 = 5$). Invariant preserved.

![Test Case 4](test_case_4_screenshot.png)

---

## 6. Deliverables and File Listing

The repository contains:
1. **`main.py`**: Complete executable Python source code containing all entity models, repositories, business logic, and CLI handlers.
2. **`flights.csv`**: 1,000-flight commercial flight database.
3. **`README.md`**: Project documentation, architecture diagrams, and setup instructions.
4. **`summary.md`**: Academic summary report detailing logic, methodology, and verification proofs.
5. **`test_case_1_screenshot.png` to `test_case_4_screenshot.png`**: Visual terminal verification evidence.

---

## 7. Conclusion

The Flight Booking Management System meets all requirements set forth in Problem Statement No. 68. The solution adheres strictly to object-oriented programming standards in Python, uses atomic file writes for transactional durability, validates all input boundaries, and maintains exact seat counts across all operations.
