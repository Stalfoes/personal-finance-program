import datetime
import matplotlib.pyplot as plt

class IncomeSource:
    def __init__(self, name:str, amount:float, date:datetime.datetime, period:datetime.timedelta=None):
        self.name = name
        self.amount = amount
        self._first_date = date
        self.period = period
    
    def __str__(self):
        return f"{self.name} +${self.amount:.2f}"

    def is_periodic(self):
        return not (self.period == None)

    def significant_datetimes_in_range(self, start:datetime.datetime, end:datetime.datetime) -> list[datetime.datetime]:
        if not self.is_periodic():
            if start <= self._first_date and self._first_date <= end:
                return [self._first_date]
        else:
            delta_from_first_date = start - self._first_date
            current_date = self._first_date + (delta_from_first_date // self.period) * self.period
            dates = []
            if start <= current_date:
                dates.append(current_date)
            current_date += self.period
            while current_date <= end:
                dates.append(current_date)
                current_date += self.period
            return dates

class Expense(IncomeSource):
    def __init__(self, name:str, amount:float, date:datetime.datetime, period:datetime.timedelta=None):
        super().__init__(name, -amount, date, period)
    
    def __str__(self):
        return f"{self.name} -${abs(self.amount):.2f}"


class BankAccount:
    def __init__(self, amount:float, starting_time:datetime.datetime, interest_rate:float, period:datetime.timedelta):
        self._starting_amount = amount
        self._starting_time = starting_time
        self.interest_rate = interest_rate
        self.period = period
        self.incomes:list[IncomeSource] = []
    
    def significant_compounding_datetimes_in_range(self, end:datetime.datetime) -> list[datetime.datetime]:
        current_date = self._starting_time + self.period
        dates = []
        while current_date <= end:
            dates.append(current_date)
            current_date += self.period
        return dates
    
    def significant_datetimes_in_range(self, end:datetime.datetime) -> list:
        compounding_dates = self.significant_compounding_datetimes_in_range(end)
        important_dates = [('compound',date) for date in compounding_dates]
        for income_source in self.incomes:
            important_dates += [(income_source.amount,date) for date in income_source.significant_datetimes_in_range(self._starting_time, end)]
        important_dates.sort(key=lambda t:t[1])
        return important_dates

    def amount_at(self, time:datetime.datetime) -> float:
        important_dates = self.significant_datetimes_in_range(time)
        money_in_account = self._starting_amount
        for date_type,important_date in important_dates:
            if date_type == 'compound':
                money_in_account *= 1 + self.interest_rate
            else:
                money_in_account += date_type
        return money_in_account
    
    def graph_account(self, start:datetime.datetime, end:datetime.datetime):
        x = [date[1] for date in self.significant_datetimes_in_range(end) if start<=date[1]]
        y = [self.amount_at(date) for date in x]
        min_amount, max_amount = min(y), max(y)
        plt.figure(figsize=(8, 4))
        plt.plot(x, y, label='Account Balance', color='black')
        for income in self.incomes:
            color = 'blue' if income.amount > 0 else 'red'
            dates = income.significant_datetimes_in_range(start, end)
            if len(dates) > 0:
                plt.vlines(x=dates, ymin=min_amount, ymax=max_amount, label=str(income), color=color, linestyles='dashed')
        plt.legend()
        plt.show()

    def average_in_out_over_period(self, length:datetime.timedelta, num_lengths:int=100) -> tuple[float,float]:
        ins = [0 for _ in range(num_lengths)]
        outs = [0 for _ in range(num_lengths)]
        for period in range(num_lengths):
            start = self._starting_time + period * length
            end = self._starting_time + (period + 1) * length
            for income in self.incomes:
                num_times = len(income.significant_datetimes_in_range(start, end))
                if income.amount > 0:
                    ins[period] += income.amount * num_times
                elif income.amount < 0:
                    outs[period] += abs(income.amount) * num_times
        a_ins = (sum(ins) / len(ins)) if len(ins) > 0 else 0.0
        a_outs = (sum(outs) / len(outs)) if len(outs) > 0 else 0.0
        return a_ins, a_outs

    def add_income(self, income:IncomeSource):
        self.incomes.append(income)
    
    def add_expense(self, expense:Expense):
        self.incomes.append(expense)


if __name__ == '__main__':
    account = BankAccount(1000, datetime.datetime.now(), 0.00, datetime.timedelta(days=365.25//4))
    luke_job = IncomeSource('Luke Pay', 7692.31, datetime.datetime.now(), datetime.timedelta(weeks=2))
    mu_job = IncomeSource('Mu Pay', 3425.73, datetime.datetime(year=2023,month=11,day=7), datetime.timedelta(weeks=2))
    rent = Expense('Rent', 1200, datetime.datetime(year=2023,month=11,day=16), datetime.timedelta(days=31))

    account.add_income(luke_job)
    account.add_income(mu_job)
    account.add_expense(rent)

    print(f"Over 2 week period:  {(a:=account.average_in_out_over_period(datetime.timedelta(weeks=2)))[0]}, {a[1]}")
    print(f"Over 1 month period: {(a:=account.average_in_out_over_period(datetime.timedelta(days=31)))[0]}, {a[1]}")
    print(f"Over 1 year period:  {(a:=account.average_in_out_over_period(datetime.timedelta(days=365.25)))[0]}, {a[1]}")

    account.graph_account(datetime.datetime.now(), datetime.datetime(year=2023,month=12,day=31))