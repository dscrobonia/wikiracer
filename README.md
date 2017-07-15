# Wikiracer

The goal of this project is to find the path connecting any two Wikipedia pages, using only the links in the articles. The solution has been implemented as a REST API.

### Solution Overview
This project approaches the problem with a multithreaded bidirectional best-first search. To do so we create Racers, each running in their own thread. There will be two Racers that start on each end of the path. Each Racer will find all links related to their target page, then find all links related to those links, and so on as it follows the possible paths. If a Racer finds a link that the opposite Racer has already traversed, then a path has been found that connects the two pages.

Because of the one-directional nature of links, however, Racers beginning at the start and end pages have to approach the problem differently. For example, just because you can traverse from Randy Savage to Dexter's Laboratory, does not mean you can go from Dexter's Laboratory to Randy Savage. This means the back facing Racer, the Racer starting at the end, has to check that each link is bidirectional before adding it as a potential path.

To optimize the search there are two main strategies used by the forward facing Racer to determine 'best-first'. First, a hard coded list of countries and [highly-connected pages](http://mu.netsoc.ie/wiki/) are used to help increase the breadth of the search. Any link matching these lists (or their children) will be given a higher priority. Second, if a link is related to the back Racer it is given higher priority to help with the depth of the search. Although the back Racer cannot use links that are not bidirectional, it does keep track of all the pages it has visited. These pages are marked as 'related' to the back Racer. If a forward facing link matches with one of these related pages it is likely more relevant to the search than other links and it is given a higher priority. Related > Hard Coded List > Neither.

### Architecture
There are only 3 files of note.

- The api.py script starts the REST server, handles requests, performs input validation, and then passes the parameters to the driver.py script

- The driver.py script takes start page, end page, and optionally the timeout and sets up two running Racer threads. The threads use shared structures for much of their processing, so the driver script creates shared caches, queues, and a result dict to hold this information. It then initializes the racers, starts the threads, and waits for them to process. If they timeout, the driver will kill them. Finally it returns the results of the search to the API.

- The racer.py script holds the Racer class. A Racer runs as a thread and crawls through links using a best-first search. The Racer starts at the page and works in the direction specified in the constructor. There is a single class for Racers going forward or backwards. The Racer's run method pulls links off of the queue, finds links embedded in those pages, ranks the newly discovered links, and then adds them back into the priority queue as well as to a cache of visited pages. If a discovered link is in the cache of the opposite running Racer, then a solution has been found, and the path can be described by recursively running back through the caches.
 
Further information about the architecture can be seen in comments of the file.


### Dependencies
- [Python 2.7](https://www.python.org/download/releases/2.7/)
- [Web.py](http://webpy.org/)

### How to Run
To start the REST server use
```
python api.py
```
The server will start up at localhost:8080 by default. If you want to change the port use
```
python api.py 8044
```
Requests can be made to the /race end point. Parameters include:
- start (required) : the title of the Wikipedia article to start from
- end (required) : the title of the Wikipedia article to end on 
- timeout (optional) : time in seconds before giving up on the search (60 seconds by default)

Example Requests:
```
http://localhost:8080/race?start=Wolf&end=Pokémon
http://localhost:8080/race?start=Smoothie%20King&end=Altoids
http://localhost:8080/race?start=Smoothie%20King&end=Altoids&timeout=30
```

Also available via docker at dscrobonia/wikiracer:1.1
```
docker run -p 8080:8080 dscrobonia/wikiracer
```

### Strategies Attempted

The first approach was to use a straight bidirectional BFS, with a thread starting on each end of the search. This worked okay for some searches, but slow for others.

To improve the breadth of the search I added a hard-coded list of [highly connected pages](http://mu.netsoc.ie/wiki/_) to crawl first. This worked extremely well, until I relized I hadn't considered the one-wayness of the links. I was discovering paths where both Altoids and Pokémon could get to Candy, but you couldn't necessarily get from Candy to Pokémon.

The next approach was to check each link for bidirectionality in the back facing Racer. This slowed the search down incredibly, as would be expected, as there was a significant increase in network requests.

To solve this requests were batched to reduce the amount of time spent over the network. Instead of a single link at at time, batches of 10-50. Additionally I switched off of the requests library, instead manually openning the connection to en.wikipedia.org and setting GET requests via the httplib library. Although requests makes the process simpler and cleaner, it has to reconnect to the host for every request which means that is has to renegotiate a TLS connection which is a very time consuming process. These two optimizations resulted in a markedly reduced time spent over the network.

To improve the performance of the actual search itself, the 'related pages' ranking of the search was added. To do this, first all of the pages visited by the back facing Racer that weren't bidirectional were tracked. These pages, though not possible links for a solution, are more closely related to end page and can help serve as a compass. The forward facing Racer will then prioritize crawling through links that match with these related pages. This helps to turn the BFS nature of the search into a DFS.


### Time Spent
- 4 - 6 hours on the first iteration
- 2 hours request batching and swithching to httplib
- 4 - 6 hours adding bidirectional checking & batching
- 2 hours adding REST API and driver
- 1 hour cleaning up and adding helpful comments
- 2 hours on unit tests
- 1 hour on readme

### To Do
- add more unit tests
- enable multiple start threads
