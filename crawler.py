from crawlingo import Crawlingo

seed = 1336829 #me, my id on Duolingo

duocrawler = Crawlingo()

# PHASE 1 - Crawl your social graph from Duolingo
duocrawler.crawl(seed, 7, seed_name = 'mattiamattia')

# PHASE 2 - After crawling, you can get social media data (Facebook and Google+ for now)  to enrich your graph information with public data avaiable.

#duocrawler.getProfilesInfo()
