
# Anvesha - Web Security Proxy Desktop App

Anvesha is a Python-based desktop application built with PyQt5 that functions as a comprehensive web security proxy tool. It leverages an integrated mitmproxy backend to intercept, inspect, manipulate, replay, and bulk-send HTTP/S requests. Anvesha is designed to assist security professionals and developers in analyzing web traffic with a user-friendly graphical interface and flexible request handling capabilities.

---

## Key Features

### Proxy Config Tab
- Start and stop the proxy server by specifying host and port.
- Display the location of the mitmproxy CA certificate for enabling HTTPS interception.
- Export a selected request from the logger as an OpenAPI 3.0 JSON specification.
- Import and export the entire application data (all logged requests and replay data) as JSON for persistence and transfer.

### Request Logger Tab
- Continuously logs all proxied HTTP/S requests and responses.
- Displays a table with columns: Request ID (shortened), Timestamp, Request Details, and Response Details.
- Supports filtering logged requests with search and clear controls.
- Buttons to send selected requests to Replay or Bulk Sender tabs for further manipulation.

### Replay Tab
- Multiple editable tabs allowing users to modify and resend HTTP requests independently.
- Each tab shows editable Request and read-only Response panels.
- Supports import/export of all replay tabs’ data.
- Functionality to capture and save screenshots of the app window.
- Button to send the current tab’s request to the Bulk Sender tab.

### Bulk Sender Tab
- Three clear sections:
  - Request Template editor with `{keyword}` placeholder.
  - Values editor (one replacement value per line).
  - Keyword input field (without braces).
- Send bulk requests by replacing `{keyword}` with each value, showing detailed results.
- Send bulk requests results to Replay as separate tabs.
- Supports receiving requests from other tabs via an `add_request()` method.
- URL parsing and sanitization to avoid connection errors.

---

## Technical Components and Architecture

- **PyQt5 UI Framework:** Modern, signal-slot based, with proper widget layouts.
- **Mitmproxy Integration:** Proxy is run as a separate subprocess controlled by the app.
- **IPC (Inter-Process Communication):** Unix socket communication between mitmproxy addon and the main app for real-time flow data.
- **Modular Widgets:** Separate components for Logger, Replay, Bulk Sender, and Proxy Config facilitate maintainability.
- **Robust Request Parsing:** Utilities for converting between raw HTTP text and structured request/response dictionaries.
- **Multithreading:** Proxy flow data is received asynchronously without blocking the UI.

---

## Setup and Installation

### Prerequisites
- **Python 3.8+**
- **pip** package manager
- **mitmproxy** installed and accessible in your environment (`mitmdump` command)

### Required Python Packages
Install dependencies using pip:


