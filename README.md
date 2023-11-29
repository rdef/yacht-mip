# yacht-mip

**Yet Another Computational HASS Tool for the Mobile Investigation of Platforms** or **yacht-mip** is a relatively easy to use tool for researchers to annotate social posts into a research database from a mobile phone. For the uninitiated, HASS stands for Humanities and Social Sciences.

**yacht-mip** is currently in development. The current release is _not functional_. The current release has been made in order to snapshot the project in its current form for posterity.

**yacht-mip** is designed to act as a mid-level technical solution that provides lightweight automation for researchers studying social platforms by creating a quick way to select and code social data. **yacht-mip** works by allowing a research participant or researcher to easily share posts from social media platforms into a research database and to conduct [qualitative coding](https://en.wikipedia.org/wiki/Coding_(social_sciences)) on the fly, then making data accessible for analysis using either **pandas** or by exporting to spreadsheets.

**yacht-mip** relies on Telegram in order to operate, and all users will need an account in order to contribute or receive data. Telegram does have spammy bots, so I recommend hardening your accounts against spam after signup.

**yacht-mip** only provides mild automation. It is not a tool for researchers wanting to grab arbitrary data at scale. It has no crawlers in place. If you are a looking for a research tool for scalar study of platforms I recommend starting with [SMAT-APP](https://smat-app.com/), which is very easy to use.

**yacht-mip** is not intended for gathering data about individual users, although could be repurposed in order to achieve such goals through modification of various **ships**. 

**yacht-mip** also includes a web snapshot tool that can capture some data from certain websites, currently listed in the repository's **ships** folder. 

Because of these potentials, a project lead should ensure that their research project is compliant with all relevant institutioanl policies and obligations covering research ethics, such as IRBs, HERCs, and similar.


# Basic workflow summary
The core workflow process involves an investigator who finds posts and then sends them to a dedicated Telegram chat for processing.

## Capture posts
The workflow for gathering posts is as follows:
1. Identify a post on a specific platform
2. Copy the post's link
3. Switch to the Telegram chat
4. Paste link into message
5. Optionally, use the markup format to add qualitative codes for hashtags, cashtags, and comments.
6. Send the message

## Pull data
Then, an investigator with appropriate credentials can then run **yacht-mip** to pull messages from the chat into a DataFrame.

In order to pull data a researcher must create an appropriate class object for the project known as a 'ship'. Each ship is a class object that bases the **yacht-mip** superclass, and is designed to pull data from html structure of the relevant platform. Ships for WeChat and Red are provided.

Using Red as an example, the full workflow for pulling data is:
1. Download and unpack the library to a local folder
2. Edit `YachtSample.ini` to add credentials as appropriate and rename to `Yacht.ini`
3. Import `yachtmip`
4. Create a RedShip object, targeted to a specific chat.
   `red_data = RedShip("<chat name>")`
   If `chat name` is not provided then this can be edited later
6. Complete any credential or two-factor authentication processes.
7. Initialise the project with `await red_data.initialise()`
   - This is an asychnronous method that initialises the network operations.
   - The tool confirms that the appropriate chats are available.
   - The tool then grabs all messages from the associated chat.
   - This creates an archive of processed messages
8. 



# Detailed description

## Setup

### Personnel

The workflow requires one or more **social investigators** and one **computational investigator**. A computational investigator can be a social investigator as well.

#### Social investigators
Social investigators are effectively the field researchers who will conduct datagathering by selecting content and engaging in social coding on the fly.

Social investigators have responsibility over: 
- selecting platform data
- initial qualitative coding

Additionally, if a social investigator is the project lead, they likely have these further responsibilities:
- ensuring ethics compliance
- instructing computational investigator and other social investigators on research direction and developments including coding directions such as standardising hashtags and cashtags

Social investigators require mild training and may be trusted project researchers (such as academic, analysts, or students) or may be non-trusted research participants (i.e. community members, media monitoring staff, volunteers, data donors, or paid contributors). 

#### Computational investigator
The computational investigator is the person who manages the code and is in receipt of the data from the social researchers.

The computational investigator has multiple responsibilities:
- securing and managing the research database
- setting up telegram chats and ensuring these are secure
- obtaining appropriate API credentials for Telegram
- tracking any errors, exceptions, bugs, or other complications with data entry
- discussing with social investigators about miskeyed data
- exporting data for later analysis

Additionally, if the computational investigator is the project lead, they likely have these further responsibilities:
- ensuring ethics compliance
- instructing social researchers on research direction

### Telegram chat setup

The computational investigator must have full credential access to a Telegram account and this account must have access to the chat that receives research data. Any restrictions to this account will also apply to the datagathering process. This account must be a normal user account with a phone number. There are methods for doing this with bot accounts, but this is unnecessary as bots will always be limited and will almost always see less than a user account.

#### Recommendations
- The computational investigator should set up all Telegram chats, and should be the 'owner' of the chat.
- Chat membership:
  - If social investigators are trusted researchers then collaborative chats may be fine.
  - If social investigators are research participants, volunteers, or are being compensated then a separate chat for each investigator is recommended.
    - This may be necessary in order to track contributions, avoid reciprocal influence between social investigators, identify potential research pollution from bad actors, and to ensure that external individuals are not added.
- Individual Telegram accounts for all investigators:
  - Privacy and Security:
    - Two-Step Verification: On
    - Phone number: Nobody
    - Groups and Channels: My Contacts
- Telegram chats should have the following settings:
  - Group:
    - Type: Private
    - Who can send messages?: Only Members
  - Permissions:
    - Add members: Off

Telegram credentials can be accessed and managed at [https://my.telegram.org/auth](https://my.telegram.org/auth)

## Datagathering

### Workflow for gathering posts
1. Identify post
2. Copy the post's link
3. Switch to the Telegram chat
4. Paste link into message
5. Optionally, use the markup format to add qualitative codes for hashtags, cashtags, and comments.
6. Send the message

### yacht-mip social code markup
yacht-mip uses an easy custom markup language to segment out the contents of a Telegram message into structured data. 

There are three kinds of markup used by the tool: comments, hashtags, and cashtags.

#### Comments
Comments are begin with three asterisks `***` and are for bulk copy/pasting relevant raw text into the database. Any commas `,` are transformed into semicolons `;`, and any tabs into double spaces `  `.

Comments should *always* come at the end of a message after all hashtags and cashtags. Any cashtags

Technical note: comments are pulled firstly by identifying `***` in a message, then performing a `foo.split.('***', 1)` transformation, with the second half being removed from further analysis. Comments are treated as strings, but do not receive sanitisation of any other data. 

#### Hashtags
Hashtags are for qualitative coding.

Hashtags begin with a `#` followed by letters or numbers (i.e. `#election`). An individual hashtags ends with whitespace, line returns, or any of `.,;*\` or `#`. Hashtags will be captured from one line, or multiple lines, and multiple hashtags are fine. 

New hashtags can be added arbitrarily by investigators, so some caution may be necessary regarding typos.

Technical note: hashtags are identified using the regex `#[^#,.;\s\\\*]+`.

Hashtags can be output in single cells in a spreadsheet, for example:
Posts|hashtags|other data
| :--- | :--- | :---
foo1| #foo1 #foo2 | foo...
foo2| #foo1 | foo...
foo3| #foo2 | foo...
foo4| #foo2 #foo5 | foo...

Or can be output as columns with boolean true/false, for example:
Posts|#foo|#foo|other data...
| :--- | :--- | :--- | :---
foo1| true | false | foo...
foo2| false | false | foo...
foo3| false | false | foo...
foo4| false | true | foo...

#### Cashtags
Cashtags are for more complicated metadata than hashtags. 

Cashtags begin with a `$` followed by letters or numbers; however, unlike hashtags, any further information on that line is treated as data related to the cashtag. 

Each cashtag needs its own line. Each line using a cashtag must start with a `$`. New hashtags can be added arbitrarily by investigators, so some caution may be necessary regarding typos. While cashtags can be several characters long, I recommend keeping these short to keep data entry easy. In our WeChat project, we reduced key metadata to single characters; i.e. we implemented 'likes' as `$l`.

Technical note: Cashtags are identified using the regex `^\$([a-zA-Z]{1,})\W(.*?)$`

Hashtags can be output as columns with boolean true/false, for example:
Posts|$wows|$likes|other data...
| :--- | :--- | :--- | :---
foo1| 0 | 0 | foo...
foo2| 1 | 0 | foo...
foo3| 12 | 193 | foo...
foo4| 0 | 4 | foo...

### Sample message markup
Below is a sample data entry message from our project studying WeChat in Australia. 

```
https://mp.weixin.qq.com/s/[snip]

#immigration #humanitarian #chinese

$v 1447
$l 4
$w 4
***Post has high clickthrough but low engagement and may not represent community interest
```

These can be broken down easily into the constituent elements

**URL**

`https://mp.weixin.qq.com/s/[snip]` is the url. 'Snip' refers to the anonymised slug that is used for basing an entry in the database.

**Hashtags**

`#immigration #humanitarian #chinese` are the hashtags noted in the database.

**Cashtags**
```
$v 1447
$l 4
$w 4
```
These cashtags identify different metadata found in the article that cannot be extracted through webaccess. For our project these `$v` refers to 'views', `$l` refers to 'likes' and `$w` refers to 'wows'. Single letters were used for simplicity's sake.


# Principles

## Practical problem space

### Sandboxing

Modern phone systems (iOS and Android) engage in a process called 'sandboxing' that prevents apps from being able to access data in other apps. This is a good thing, as we want our personal information to remain private to its specific context. In other words, we don't want social media apps, banking apps, and scummy games to share information. 

The complication is that if an academic researcher wants to study behaviour on a mobile platform then it can be difficult to access app data at scale. While this sandboxing can be overcome by skilled software developers, it remains non-trivial, and research tools are often expensive to produce and highly protected. 

### API factors

This project began as a study of news publication on WeChat in advance of the 2022 Australian election. The API for WeChat is designed for small business operators, and is not suitable for researchers. However, because WeChat makes its news publications shareable on the open web via standard urls, we had a useful reference point for basing our research project, and a way of accessing content from desktop computers if necessary, without requiring logins. 

This same method can be reused for any other platform that makes any of its content available on the open web, such as the non-private aspects of YouTube, Xiaohongshu, Reddit, Instagram, and other sites.

After we resolved the project's focus on the Australian election period, several major platforms killed off API access. This impacted research on these platforms, which meant many existing research methods could not continue. Fortunately, as the **yacht-mip** tool does not require API access to the platforms, it is easy to continue studying these platforms.

This method is likely to continue working until Telegram substantially changes its API operations.

See my research paper on the ethics impacts of API vs. scraping for further commentary on this matter.


## Methodological problem space

**yacht-mip** is specifically intended to enabled focused, human-level selection and coding of data from social platforms in order to enable qualitative HASS research. 

It is designed to avoid widespectrum data gathering from these services, and to avoid shifting projects into quantitative research as this is not be desirable to all researchers.

Existing HASS research methodologies for studying mobile phone cultures span a spectrum of automation from low-level to high-level. Low-level methods are useful and reliable, but can be time intensive - for instance, research projects that rely on screenshot methodologies. High-level solutions are less accessible to HASS scholars, especially those without substantial technical skills in networking or programming. High-level solutions also provide valuable scale and quantification, they tend to provide less for models of research that are driven by critical social inquiry. Highly technical systems are difficult to use and access, and are expensive to build, and are thus a problem for those without research grants. There is also a gap in access to qualitative tools; many data capture systems are quant-focused, and alternatives are likely to arise that use AI (and probably already have) which will take researchers away from close personal focus on humanistic data.

# **yacht-mip** project history

## Version history

**yacht-mip** is the second iteration of this tool, completely rewritten using a class system. The earlier version, which was never released, was a first attempt, and highly conditioned to studying WeChat. 

## Project goals

- Implement data export for:
  - [ ] xlsx
  - [ ] CSV
- Ships for:
  - [x] WeChat
  - [x] Xiaohongshu (Red)
  - [ ] Reddit
  - [ ] Bluesky
  - [ ] Twitter

