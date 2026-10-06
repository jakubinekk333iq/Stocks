import tkinter as tk
import random

class StockGame:
    def __init__(self, root):
        self.cash = 10000.0
        self.start_cash = 10000.0
        self.portfolio = {}
        self.stocks = {"AAPL": 150.0, "TSLA": 200.0, "MSFT": 300.0}
        self.locked_stocks = {"AMZN": 120.0, "GOOG": 140.0, "NVDA": 180.0}
        self.colors = {
            "AAPL": "#e74c3c",
            "TSLA": "#3498db",
            "MSFT": "#2ecc71",
            "AMZN": "#f39c12",
            "GOOG": "#9b59b6",
            "NVDA": "#1abc9c"
        }
        self.history = {s: [p] for s, p in self.stocks.items()}

        # Time system: each tick is one hour
        self.day = 1
        self.hour = 0

        self.active_ticker = "AAPL"
        self.selected_qty = 1
        self.forced_changes = {}

        # Insider tip scheduled price paths:
        # ticker -> list of future hourly prices
        self.scheduled_paths = {}

        self.tick_ms = 3000

        self.root = root
        self.root.title("Minimalist Stocks")
        self.root.geometry("450x660")
        self.root.configure(bg="#f4f6f8")

        # Chart
        self.canvas = tk.Canvas(root, bg="#ffffff", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=15, pady=(15, 5))

        # Info & Status
        self.info_lbl = tk.Label(
            root,
            text="",
            font=("Helvetica", 10, "bold"),
            bg="#f4f6f8",
            fg="#2c3e50"
        )
        self.info_lbl.pack(pady=5)

        self.status_lbl = tk.Label(
            root,
            text="Welcome! Each tick is 1 hour; markets update every 3s.",
            font=("Helvetica", 10),
            bg="#f4f6f8",
            fg="#7f8c8d"
        )
        self.status_lbl.pack()

        # Stock Selector
        self.selector_frame = tk.Frame(root, bg="#f4f6f8")
        self.selector_frame.pack(pady=10)
        self.stock_buttons = {}
        for ticker in self.stocks:
            self.add_stock_button(ticker)

        # Portfolio Text
        self.text = tk.Text(
            root,
            height=6,
            width=35,
            state=tk.DISABLED,
            bg="#ffffff",
            fg="#2c3e50",
            font=("Courier", 11),
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#e0e0e0"
        )
        self.text.pack(pady=5)

        # Quantity Buttons
        qty_frame = tk.Frame(root, bg="#f4f6f8")
        qty_frame.pack(pady=5)
        tk.Label(
            qty_frame,
            text="Qty:",
            bg="#f4f6f8",
            fg="#2c3e50",
            font=("Helvetica", 10)
        ).pack(side=tk.LEFT, padx=5)

        self.qty_buttons = {}
        for q in [1, 5, 10, 20, 50]:
            btn = tk.Button(
                qty_frame,
                text=str(q),
                font=("Helvetica", 9, "bold"),
                width=3,
                command=lambda val=q: self.select_qty(val),
                relief=tk.FLAT,
                cursor="hand2",
                bg="#e0e0e0",
                fg="#2c3e50"
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.qty_buttons[q] = btn
        self.update_qty_selector_ui()

        # Action Buttons
        btn_frame = tk.Frame(root, bg="#f4f6f8")
        btn_frame.pack(pady=(10, 2))

        btn_style = {
            "font": ("Helvetica", 10, "bold"),
            "width": 8,
            "relief": tk.FLAT,
            "cursor": "hand2"
        }

        tk.Button(
            btn_frame,
            text="BUY",
            bg="#2ecc71",
            fg="white",
            command=lambda: self.trade('b'),
            **btn_style
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            btn_frame,
            text="SELL",
            bg="#e74c3c",
            fg="white",
            command=lambda: self.trade('s'),
            **btn_style
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            btn_frame,
            text="SHOP",
            bg="#f39c12",
            fg="white",
            command=self.open_shop,
            **btn_style
        ).pack(side=tk.LEFT, padx=3)

        # Sell All Button
        tk.Button(
            root,
            text="SELL ALL SELECTED",
            bg="#c0392b",
            fg="white",
            command=self.sell_all,
            font=("Helvetica", 9, "bold"),
            width=30,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(pady=(0, 10))

        self.root.bind("<Configure>", lambda e: self.draw_chart())
        self.update_stock_selector_ui()
        self.update_ui()

        # Start automatic hourly updates
        self.root.after(self.tick_ms, self.auto_tick)

    def auto_tick(self):
        self.next_hour()
        self.root.after(self.tick_ms, self.auto_tick)

    def select_qty(self, qty):
        self.selected_qty = qty
        self.update_qty_selector_ui()

    def update_qty_selector_ui(self):
        for q, btn in self.qty_buttons.items():
            if q == self.selected_qty:
                btn.config(bg="#34495e", fg="white")
            else:
                btn.config(bg="#e0e0e0", fg="#2c3e50")

    def add_stock_button(self, ticker):
        btn = tk.Button(
            self.selector_frame,
            text=ticker,
            font=("Helvetica", 10, "bold"),
            command=lambda t=ticker: self.select_stock(t),
            width=6,
            relief=tk.FLAT,
            cursor="hand2",
            bg="#e0e0e0",
            fg="#2c3e50"
        )
        btn.pack(side=tk.LEFT, padx=3)
        self.stock_buttons[ticker] = btn

    def select_stock(self, ticker):
        self.active_ticker = ticker
        self.update_stock_selector_ui()
        self.set_status(f"Selected {ticker}")

    def update_stock_selector_ui(self):
        for t, btn in self.stock_buttons.items():
            if t == self.active_ticker:
                btn.config(bg="#34495e", fg="white")
            else:
                btn.config(bg="#e0e0e0", fg="#2c3e50")

    def _make_price_path(self, start_price, hours):
        """Create a forced future price path for insider tips."""
        price = start_price
        path = []
        for _ in range(hours):
            price = max(1.0, price * (1 + random.uniform(-0.05, 0.05)))
            path.append(price)
        return path

    def update_prices(self):
        for s in list(self.stocks.keys()):
            # Forced pump/dump effects take priority
            if s in self.forced_changes:
                multiplier = self.forced_changes.pop(s)

                # If there is an insider path, scale its remaining path
                if s in self.scheduled_paths and self.scheduled_paths[s]:
                    self.scheduled_paths[s] = [
                        max(1.0, price * multiplier)
                        for price in self.scheduled_paths[s]
                    ]
                    new_price = self.scheduled_paths[s].pop(0)
                    if not self.scheduled_paths[s]:
                        del self.scheduled_paths[s]
                else:
                    new_price = max(1.0, self.stocks[s] * multiplier)

            # Insider tip scheduled path
            elif s in self.scheduled_paths and self.scheduled_paths[s]:
                new_price = max(1.0, self.scheduled_paths[s].pop(0))
                if not self.scheduled_paths[s]:
                    del self.scheduled_paths[s]

            # Normal random movement
            else:
                new_price = max(
                    1.0,
                    self.stocks[s] * (1 + random.uniform(-0.05, 0.05))
                )

            self.stocks[s] = new_price
            self.history[s].append(new_price)

            if len(self.history[s]) > 60:
                self.history[s].pop(0)

    def set_status(self, msg, is_error=False):
        self.status_lbl.config(
            text=msg,
            fg="#e74c3c" if is_error else "#2ecc71"
        )

    def trade(self, action):
        ticker = self.active_ticker
        amt = self.selected_qty

        price = self.stocks[ticker]

        if action == 'b':
            cost = amt * price
            if cost > self.cash:
                self.set_status("Error: Insufficient funds.", True)
            else:
                self.cash -= cost
                self.portfolio[ticker] = self.portfolio.get(ticker, 0) + amt
                self.set_status(f"Bought {amt} {ticker} @ ${price:.2f}")
        else:
            if amt > self.portfolio.get(ticker, 0):
                self.set_status(f"Error: Not enough {ticker} shares.", True)
            else:
                self.cash += amt * price
                self.portfolio[ticker] -= amt
                self.set_status(f"Sold {amt} {ticker} @ ${price:.2f}")

        self.update_ui()

    def sell_all(self):
        ticker = self.active_ticker
        amt = self.portfolio.get(ticker, 0)

        if amt <= 0:
            self.set_status(f"Error: No {ticker} shares to sell.", True)
        else:
            price = self.stocks[ticker]
            self.cash += amt * price
            self.portfolio[ticker] = 0
            self.set_status(f"Sold all {amt} {ticker} @ ${price:.2f}")

        self.update_ui()

    def next_hour(self):
        self.hour += 1

        if self.hour >= 24:
            self.hour = 0
            self.day += 1

        self.update_prices()
        self.set_status(f"Day {self.day} {self.hour:02d}:00 - Prices Updated")
        self.update_ui()

    def open_shop(self):
        shop = tk.Toplevel(self.root)
        shop.title("Shop")
        shop.geometry("280x380")
        shop.configure(bg="#f4f6f8")

        tk.Label(
            shop,
            text="MARKET SHOP",
            font=("Helvetica", 14, "bold"),
            bg="#f4f6f8",
            fg="#2c3e50"
        ).pack(pady=15)

        items = [
            {"name": "Unlock AMZN", "cost": 1500, "type": "stock", "ticker": "AMZN"},
            {"name": "Unlock GOOG", "cost": 2000, "type": "stock", "ticker": "GOOG"},
            {"name": "Unlock NVDA", "cost": 2500, "type": "stock", "ticker": "NVDA"},
            {"name": "Insider Tip (Next Day)", "cost": 400, "type": "boost_tip"},
            {"name": "Market Pump (+15%)", "cost": 800, "type": "boost_pump"},
            {"name": "Cash Dividend (+$1000)", "cost": 600, "type": "boost_cash"}
        ]

        for item in items:
            if item["type"] == "stock" and item["ticker"] in self.stocks:
                continue

            frame = tk.Frame(shop, bg="#f4f6f8")
            frame.pack(pady=6, fill=tk.X, padx=20)

            tk.Label(
                frame,
                text=f"{item['name']}\n${item['cost']}",
                bg="#f4f6f8",
                fg="#2c3e50",
                justify=tk.LEFT,
                font=("Helvetica", 9)
            ).pack(side=tk.LEFT)

            tk.Button(
                frame,
                text="Buy",
                command=lambda i=item, w=shop: self.buy_item(i, w),
                bg="#2ecc71",
                fg="white",
                relief=tk.FLAT,
                width=6,
                font=("Helvetica", 9, "bold")
            ).pack(side=tk.RIGHT)

    def buy_item(self, item, shop_window):
        if self.cash < item["cost"]:
            self.set_status("Not enough cash for shop item!", True)
            return

        self.cash -= item["cost"]

        if item["type"] == "stock":
            t = item["ticker"]
            self.stocks[t] = self.locked_stocks[t]
            self.history[t] = [self.locked_stocks[t]]
            del self.locked_stocks[t]
            self.add_stock_button(t)
            self.update_stock_selector_ui()
            self.set_status(f"Unlocked {t}!")

        elif item["type"] == "boost_tip":
            t = self.active_ticker
            path = self._make_price_path(self.stocks[t], 24)
            self.scheduled_paths[t] = path
            self.set_status(
                f"INSIDER TIP: {t} should be ~${path[-1]:.2f} in 24h."
            )

        elif item["type"] == "boost_pump":
            self.forced_changes[self.active_ticker] = 1.15
            self.set_status(f"Market Pump active for {self.active_ticker}!")

        elif item["type"] == "boost_cash":
            self.cash += 1000
            self.set_status("Dividend paid! +$1000 cash.")

        self.update_ui()
        shop_window.destroy()
        self.open_shop()

    def draw_chart(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        if w < 50 or h < 50:
            return

        for i in range(1, 4):
            y = (h / 4) * i
            self.canvas.create_line(0, y, w, y, fill="#ecf0f1", width=1)

        all_prices = [p for prices in self.history.values() for p in prices]
        if not all_prices:
            return

        min_p, max_p = min(all_prices), max(all_prices)
        if min_p == max_p:
            max_p = min_p + 10

        for ticker, prices in self.history.items():
            color = self.colors.get(ticker, "black")
            points = []

            for i, p in enumerate(prices):
                x = (i / max(1, len(prices) - 1)) * w if len(prices) > 1 else w / 2
                y = h - ((p - min_p) / (max_p - min_p)) * (h - 40) - 20
                points.extend([x, y])

            if len(points) >= 4:
                self.canvas.create_line(points, fill=color, width=2.5, smooth=False)

        legend_y = 15
        for i, (ticker, color) in enumerate(self.colors.items()):
            if ticker in self.stocks:
                x = 15 + (i * 70)
                self.canvas.create_rectangle(
                    x,
                    legend_y - 5,
                    x + 10,
                    legend_y + 5,
                    fill=color,
                    outline=""
                )
                self.canvas.create_text(
                    x + 18,
                    legend_y,
                    text=ticker,
                    anchor=tk.W,
                    fill="#2c3e50",
                    font=("Helvetica", 9, "bold")
                )

    def update_ui(self):
        net_worth = self.cash + sum(
            self.portfolio.get(s, 0) * p for s, p in self.stocks.items()
        )
        profit = net_worth - self.start_cash
        profit_str = f"+${profit:.2f}" if profit >= 0 else f"-${abs(profit):.2f}"

        self.info_lbl.config(
            text=(
                f"D{self.day} {self.hour:02d}:00  |  "
                f"Cash: ${self.cash:,.2f}  |  "
                f"Net: ${net_worth:,.2f} ({profit_str})"
            )
        )

        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)

        for s, p in self.stocks.items():
            owned = self.portfolio.get(s, 0)
            self.text.insert(tk.END, f" {s:<5} ${p:>7.2f}   Owned: {owned:<4}\n")

        self.text.config(state=tk.DISABLED)

        self.draw_chart()


if __name__ == "__main__":
    root = tk.Tk()
    StockGame(root)
    root.mainloop()