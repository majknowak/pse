# PSE Price Monitor
Event-triggered script to notify end users about electricity price changes in Poland.

## How it started

A friend asked me if it's possible to get SMS notifications once the electricity 
price in Poland goes negative. He reached out to me since PSE - Polskie Sieci 
Elektroenergetyczne (organization responsible for electricity transmission) - 
publishes this data in a [Power BI Dashboard](https://raporty.pse.pl/?report=SK-D&state=Funkcjonowanie%20RB,Raporty%20dobowe%20z%20funkcjonowania%20RB,Oferty%20bilansuj%C4%85ce,Ilo%C5%9B%C4%87%20energii%20bilansuj%C4%85cej%20i%20niezbilansowania,Podstawowe%20wska%C5%BAniki%20cenowe%20i%20kosztowe&date=2024-10-31&type=table).

Of course, we cannot set up any alerts on a dashboard that's not owned by us…
But it turned out PSE publishes the same kind of information via API 😍

This way, I was able to use my little Python knowledge to come up with a solution 
that does the job perfectly.

## What's it all about?

### AS IS

The end user is interested in tracking the electricity prices published in the 
report mentioned earlier:

![1.png](https://github.com/majknowak/pse/blob/943b45ef28cb6f69f82c918b28620257c083d3e5/screenshots/1.png)

The thing is, this view reports data in 15-minute intervals, which you probably 
don't want to check manually so often.

### TO BE

Build an automated solution to check if the current price goes below 0 and, 
if so, send an SMS. Keep tracking, and do the same if the price becomes greater 
than 0 again.

Sounds like a perfect real-world implementation for a guy like me 😃

## Project description

Here's a quick summary of what the code actually does:

### API Request

The code checks the same kind of information as provided in the Power BI Dashboard:

![2.png](https://github.com/majknowak/pse/blob/fcfe98ea187f35b7a72cc48c19f8ff49a1a88b77/screenshots/2.png)

### Process Records

For our use case, it's enough to just check the last two available price records:

- If both of them are negative or both are positive, no action is triggered.
- If there is a move from positive to negative or vice versa, the `send_sms` function is triggered.
- Depending on the price, the SMS body indicates to the end user if it just became positive or negative.

### Logging and "Spam" Prevention

There are a few more features covering logging and, more importantly, preventing the script from notifying the user about the same price event multiple times:

- A separate `state.json` file stores the last "state," meaning the price record that triggered the notification. It is used for comparison between the currently processed price record, and only if the current one is different from the saved one the new notification triggered. 😊

### Scheduled Execution

The script is stored at [PythonAnywhere](https://www.pythonanywhere.com/) to enable scheduled execution. This way, I can run it every few minutes to ensure none of the price updates are missed, as they sometimes occur irregularly.

### SMS Notifications

For SMS notifications, I've used [Twilio](https://www.twilio.com/en-us). It's easy to set up and not very costly.

That's it! Simple but doing the job!

---

## Update — Early 2026

A few things changed since the initial release in late 2024, so it was time for an update.

### PSE improved their reporting

PSE released a much nicer dashboard in early 2026 — with proper charts, date range pickers and a cleaner interface. A big improvement over the table-based Power BI report we started with:

![3.png](https://github.com/majknowak/pse/blob/main/screenshots/3.png?raw=true)

You can check it out here: [PSE Price Dashboard](https://raporty.pse.pl/report/bpci-energy-and-prices?chart=true&bpciDataType=FCST&dateFrom=2026-03-18&dateTo=2026-03-18)

### PSE API Update

Along with the new dashboard, PSE also updated their API. The old endpoint we relied on was replaced, which meant our script needed updating too. Not a bad thing — the new API is cleaner and returns more useful data.

### What changed in the script

- Updated to the new PSE API endpoint
- Switched to Polish local time for cleaner logs and SMS messages
- Added support for multiple SMS recipients
- Script now runs as an always-on task with a 2-minute sleep loop — more efficient than scheduled tasks
- Active hours window added (08:30–19:30 Warsaw time) to focus checks during relevant hours
- Lightweight Flask web app added for remote log viewing from any browser

See [CHANGELOG.md](CHANGELOG.md) for full technical details.

```
