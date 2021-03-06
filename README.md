# FHLB SF API

API interface to a subset of the Federal Home Loan Bank of San Francisco's reporting capabilities via their website.

## Rationale
The Federal Home Loan Bank of San Francisco provides access via it's website to a plethora of member-bank data, however there is currently no programmatic interface to access this data.  Several reports are available in Excel/CSV format or PDF format, but this still requires logging into the website, pulling down the data, and parsing it before any work can be done.  This project is meant to wrap certain portions of the website in a programmer friendly API simlar to what it may look like as a REST API.

## Installation
You can install this package either with `pip install fhlb`, or clone this repository and run `python setup.py install` from the top level directory where `setup.py` is located.

## Limitations
#### Limited Coverage of Available Data
For now, the main areas of focus will be a subset of the reporting tab within the FHLB website.  Currently supported reports include:
- Advances data
- Current and Historical Indicative Rates
- Settlement/Transaction Account Status
- Borrowing Capacity
- Letters of Credit

There are of course, several additional reports and further many more sections of the website outside of the reporting region which may not be covered initially by this project. Available reports may be slowly expanded, but other areas will likely not be updated in the near future until the need arises (e.g. if others find it useful).
#### Fragility
Since there is no official API yet, the data is pulled by scraping the website - similar to what mint.com or other financial aggregators have done in the past when there are no API's available.  The consequence is that if the site changes, so to must this program.  Aggregators like mint.com have a team of people to keep their program in sync with websites, whereas for this project you have just me :)
#### Speed of Execution
Unfortunately try as I may, I was unable to find the actual endpoints where the data lives, e.g. those endpoints hit internally by the FHLB when they receive a request and pass it along to their server.  In order to retrieve data from the FHLB website, I'm using `selenium` with the `phantomJS` headless browser to simulate actual browser actions.  Browser automation is not the fastest way to retrieve data - everything you do is performed on one thread, synchronously, using one `WebDriver`. Creating a WebDriver instance and logging in takes some time, so the first request you make will take somewhere around 10-20 seconds.  Subsequent requests happen considerably faster since the WebDriver has already logged in and that point and simply needs to jump to new URL's.  Given that most of the data reflects historical information, I don't paritcularly view this as a limitation since we are not interested in processing data in real-time, however it is something I wanted to point out in case you may be wondering why the requests seem slow to start. In the future I may explore a multiple WebDriver approach where each driver is on a different thread, distributing the workload across those thread-specific drivers. However, since most of the time is spent initially creating the driver I'm not certain how much this will benefit overall execution time.  
## Dependencies
There is one external dependency you will need to download: `PhantomJS`.  If you're on a mac, you can run `brew install phantomjs`.  For other operating systems, visit the [PhantomJS website](http://phantomjs.org/download.html) and download the appropriate file.

## Configuration
In the `config.py` file, there are two variables present, each of which may be left empty: 
 - `SERVICE_ARGS`
    -  list of arguments passed to the webdriver and handles things like proxy auth, log file path, ssl protcol, etc.  
 - `PHANTOM_JS_PATH`
    -  location of the `PhantomJS` executable, if left empty will default to `path`. If the executable is not on your path you must provide the location of the `.exe` (full path including the extension).

## Future Work
- Add additional endpoints in the reporting section of the FHLB website and elsewhere
- Consider multiple drivers on separate threads (startup time for drivers will still be an issue)

## Examples
Provided below are example requests and sample response data.  Any figures referenced below are strictly for examples sake and not meant to reflect meaningful data (e.g. rates, balances, etc. are made up).

##### Initialize the client with website username and password
```python
import fhlb

# username and password correspond to the websites login page
client = fhlb.Client(username,password)

```
##### Perform requests corresponding to reporting tab
```python
# request outstanding advances
client.advances('2019-02-01')

# output
[  
   {  
      'Trade Date':'2011-05-17',
      'Funding Date':'2011-05-18',
      'Maturity Date':'2015-05-17',
      'Advance Number':329646.0,
      'Advance Type':'FRC',
      'Current Par ($)':125000000.0,
      'Interest Rate (%)':1.15,
      'Next Interest Payment Date':'2015-05-17',
      'Accrued Interest ($)':35183.15,
      'Estimated Next Interest Payment ($)':38913.3,
      'Details':'View'
   },
   {  
      'Trade Date':'2011-01-17',
      'Funding Date':'2011-01-18',
      'Maturity Date':'2015-01-17',
      'Advance Number':329646.0,
      'Advance Type':'FRC',
      'Current Par ($)':500000000.0,
      'Interest Rate (%)':1.18,
      'Next Interest Payment Date':'2015-01-17',
      'Accrued Interest ($)':125891.15,
      'Estimated Next Interest Payment ($)':124381.3,
      'Details':'View'
   },
   ...
]
 
# get STA data
client.sta_account('2019-02-01','2019-02-26')
 
# output
{  
   '2018-09-28':[  
      {  
         'Reference Number':'  ',
         'Description':'Balance as of close of business',
         'Rates (%)':1.28,
         'Debits ($)':None,
         'Credits ($)':None,
         'Balance ($)':153813.18
      },
      {  
         'Reference Number':108512.0,
         'Description':'LC MAINTENANCE_FEE 2012-85',
         'Rates (%)':None,
         'Debits ($)':150.0,
         'Credits ($)':None,
         'Balance ($)':None
      },
      {  
         'Reference Number':158913.0,
         'Description':'LC ISSUANCE_FEE 2013-50',
         'Rates (%)':None,
         'Debits ($)':99.0,
         'Credits ($)':None,
         'Balance ($)':None
      },
      {  
         'Reference Number':853218.0,
         'Description':'SECURITY SAFEKEEPING FEE',
         'Rates (%)':None,
         'Debits ($)':28.1,
         'Credits ($)':None,
         'Balance ($)':None
      }
   ],
   ...
}

# get current indicative borrowing rates
client.current_rates()

# output
{  
   'standard credit vrc':[  
      {  
         'Advance Maturity':'Overnight/Open',
         'Advance Rate (%)':1.85
      }
   ],
   'standard credit frc':[  
      {  
         'Advance Maturity':'1 Month',
         'Advance Rate (%)':1.79
      },
      {  
         'Advance Maturity':'2 Months',
         'Advance Rate (%)':1.83
      },
      ...

   ],
   'standard adjustable rate credit':[  
      {  
         'Advance Maturity':'1 Year',
         '1 Month LIBOR':8.0,
         '3 Month LIBOR':-1.0,
         '6 Month LIBOR':-10.0,
         'Daily Prime':-315.0
      },
      {  
         'Advance Maturity':'2 Years',
         '1 Month LIBOR':15.0,
         '3 Month LIBOR':0.0,
         '6 Month LIBOR':-10.0,
         'Daily Prime':-450.0
      },
      ...
   ],
   'securities-backed credit vrc':[  
      {  
         'Advance Maturity':'Overnight/Open',
         'Advance Rate (%)':1.78
      }
   ],
   'securities-backed credit frc':[  
      {  
         'Advance Maturity':'1 Month',
         'Advance Rate (%)':1.15
      },
      {  
         'Advance Maturity':'2 Months',
         'Advance Rate (%)':1.23
      },
     ...
   ],
   'securities-backed adjustable rate credit':[  
      {  
         'Advance Maturity':'1 Year',
         '1 Month LIBOR':5.0,
         '3 Month LIBOR':-8.0,
         '6 Month LIBOR':-15.0
      },
      {  
         'Advance Maturity':'2 Years',
         '1 Month LIBOR':8.0,
         '3 Month LIBOR':-9.0,
         '6 Month LIBOR':-10.0
      },
    ...
   ],
   'Settlement/Transaction Account (STA)':{  
      'Effective Rate for Prior Business Day (%)':'1.82000'
   }
}

# get historical indicative rates 
# output varies slightly for different collateral_type and credit_type combination
client.historical_rates(
	'2019-02-01',
	'2019-02-26',
	collateral_type='standard',
	credit_type='frc'
)

# output
{  
   '2019-02-01':{  
      '1 mo':1.37,
      '2 mo':1.48,
      '3 mo':1.58,
      '6 mo':1.89,
      '1 yr':2.05,
      '2 yr':2.15,
      '3 yr':2.23,
      '5 yr':2.41,
      '7 yr':2.42,
      '10 yr':2.61,
      '15 yr':2.71,
      '20 yr':2.75,
      '30 yr':2.83
   },
   '2019-02-04':{  
      '1 mo':1.37,
      '2 mo':1.47,
      '3 mo':1.58,
      '6 mo':1.88,
      '1 yr':2.04,
      '2 yr':2.14,
      '3 yr':2.23,
      '5 yr':2.41,
      '7 yr':2.42,
      '10 yr':2.62,
      '15 yr':2.70,
      '20 yr':2.74,
      '30 yr':2.82  
    ...
   }
 
# get borrowing capacity - either current-day or month-end going back 12 months
# calling with no argument defaults to current day
client.borrowing_capacity(date='2019-02-28') 

# output
{  
   'standard':{  
      'collateral':{  
         'RESIDENTIAL - ARMs':{  
            'Count':15831.0,
            'Original Amount ($)':18283192013.0,
            'Unpaid Principal Balance ($)':15358101715.0,
            'Market Value ($)':14658914761.0,
            'BC/UPB (%)':88.0,
            'Borrowing Capacity ($)':12899844990.0
         },
         'SECONDS':{  
            ....
         },
         'RESIDENTIAL - FIXED':{  
            ...
         },
         'RESIDENTIAL FIRST LIEN HELOCs':{  
            ...
         },
         'MULTIFAMILY - ARMs':{  
            ...
         },
         'COMMERCIAL':{  
            ...
         },
         'MULTIFAMILY - FIXED':{  
            ...
         },
         'RESIDENTIAL NEG AM':{  
            ...
         },
         'Totals':{  
            ...
         }
      },
      'capacity':{  
         'Less Excluded Blanket Lien Borrowing Capacity':0.0,
         'Less Excluded Bank Borrowing Capacity':0.0,
         'Less Excluded Regulatory Borrowing Capacity':0.0,
         'Net Loan Collateral Borrowing Capacity':15184081473.0,
         'Plus Securities Borrowing Capacity':0.0,
         'Total Borrowing Capacity':15184081473.0,
         'Less Advances':5000000000.0,
         'Less Letters of Credit':769316791.0,
         'Less SWAP Collateral Required':0.0,
         'Less Cover SBC Type Deficiencies':0.0,
         'Less Potential Prepayment Fees':0.0,
         'Less Other Collateral Required':0.0,
         'Less MPF CE Collateral Required':0.0,
         'Remaining Borrowing Capacity':9949230265.0
      }
   },
   'securities_backed':{  
      'collateral':{  
         'AA':{  
            'Total Market Value ($)':0.0,
            'Total Borrowing Capacity ($)':0.0,
            'Advances ($)':0.0,
            'Covered by Standard Credit ($)':0.0,
            'Excess ($)':0.0,
            'Total ($)':0.0
         },
         'AAA':{  
            ...
         },
         'Agency':{  
            ...
         },
         'Totals':{  
            ...
         }
      },
      'capacity':{  
         'Less Other Collateral Required':0.0,
         'Less Excluded Regulatory Borrowing Capacity':0.0,
         'Remaining Borrowing Capacity':0.0
      }
   }
}

# current letters of credit
client.letters_of_credit()

# output
[  
   {  
      'LC Number':'2005-018',
      'Beneficiary':'Moneybags bank, 707..',
      'Current Amount ($)':18351038.1,
      'Issue Date':'2012-01-15',
      'Expiration Date':'2015-01-15',
      'Annual Maintenance Charge (bps)':3.0,
      'CICA Credit Program':'ACE',
      'Actions':'VIEW PDF'
   },
   {  
      'LC Number':'2003-018',
      'Beneficiary':'Broke bank, 707..',
      'Current Amount ($)':100.0,
      'Issue Date':'2011-01-15',
      'Expiration Date':'2011-01-16',
      'Annual Maintenance Charge (bps)':15.0,
      'CICA Credit Program':'ACE',
      'Actions':'VIEW PDF'
   },
   ...
]
```
