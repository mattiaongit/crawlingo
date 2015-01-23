import requests, pymongo, time, json, httplib2, apiclient.discovery

class GPlusInfos:

  def __init__(self):

    API_KEY = "YOURAPIKEYHERE"

    self.plus = apiclient.discovery.build('plus','v1', http=httplib2.Http(),developerKey=API_KEY)
    self.people = self.plus.people()

    self.sleeptime = 0.3

    connection = pymongo.Connection()
    self.db = connection['duolingo']
    self.users = self.db['users']

    self.socialsinfos = self.db['socialinfos']

  def getProfiles(self):
    #stored = self.socialsinfos.find({"usernames.gplus":{"$exists":True}},{'_id':1})
    #visited_ids = [s['_id'] for s in list(stored)]
    duousers = self.users.find({'$and':[{'social_ids.facebook': {'$ne':None}},{'social_ids.gplus': {'$ne':None}}]},{'social_ids.gplus':1, 'username':1})
    toscrape = duousers.count()
    counter = 0

    print("{0} users to scrape".format(toscrape))
    #print("{0} already scraped".format(len(visited_ids)))

    while(True):
      try:
        user = duousers.next()
        print("Getting profile g+ id {0}, duolingo id : {1}".format(user['social_ids']['gplus'],user['_id']))
        counter += 1

        try:
          profile = self.people.get(userId=user['social_ids']['gplus']).execute()
        except Exception:
          print("Profile not found")
          continue

        # infos = {
        #   '_id' : user['_id']
        # }

        if 'name' in profile and 'givenName' in profile['name'] and 'familyName' in profile['name']:
          # names = { 'names': {
          #   'gplus': profile['name']['givenName'] + " " + profile['name']['familyName']
          #   }
          # }
          # infos.update(names)

          names = profile['name']['givenName'] + " " + profile['name']['familyName']
          self.socialsinfos.update({"_id":user['_id']}, {"$set": {"names.gplus": names}}, upsert=True)

        if 'displayName' in profile :
          # usernames = { 'usernames': {
          #   'duolingo' : user['username'],
          #   'gplus' : profile['displayName']
          #   }
          # }
          # infos.update(usernames)
          displayName = profile['displayName']
          self.socialsinfos.update({"_id":user['_id']}, {"$set": {"usernames.gplus": displayName}}, upsert=True)


        if 'gender' in profile:
          # gender = {'gender': profile['gender']}
          # infos.update(gender)
          gender = profile['gender']
          self.socialsinfos.update({"_id":user['_id']}, {"$set": {"gender": gender}}, upsert=True)


        if counter % 20 == 0:
          print('{0} Profiles retrived by now'.format(counter))

        time.sleep(self.sleeptime)

      except StopIteration:
        print('Done!')
        break
