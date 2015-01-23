import requests, pymongo, time, json, random

class FacebookInfos:

  def __init__(self):

    self.graph = "http://graph.facebook.com/"

    self.sleeptime = 0.8

    connection = pymongo.Connection()
    self.db = connection['duolingo']
    self.users = self.db['users']

    self.socialsinfos = self.db['socialinfos']



  def getProfile(self, id):
    response = None
    backoff = 20
    while response == None and backoff <= 160 :
      try:
        response = json.loads(requests.get(self.graph+str(id)).text)
      except Exception:
        print("Somenthing went wrong with the requests, retrying in {1} seconds. Failed id request: {0} ".format(id,backoff))
        backoff *= 2
        continue

    if response == None:
      print("Skipping this request")

    return response



  def getProfiles(self):
    stored = self.socialsinfos.find({},{'_id':1})
    visited_ids = [s['_id'] for s in list(stored)]
    duousers = self.users.find({'$and':[{'_id': {'$nin': visited_ids}},{'social_ids.facebook': {'$ne':None}},{'social_ids.gplus': {'$ne':None}}]},{'social_ids.facebook':1, 'username':1})
    toscrape = duousers.count()
    counter = 0

    print("{0} users to scape".format(toscrape))

    while(True):
      try:
        user = duousers.next()
        print("Getting profile fb id {0}".format(user['social_ids']['facebook']))
        counter += 1

        profile = self.getProfile(user['social_ids']['facebook'])

        if profile == None:
          continue

        if 'error' in profile:
          print("Error: {0}".format(profile['error']['message']))
          if 'Application request limit reached' in profile['error']['message']:
            print("Going to sleep for a while ...")
            time.sleep(900) # 15minutes span
          continue

        infos = {
          '_id' : user['_id'],
          'names': {
            'facebook': profile['name']
          }
        }

        if 'username' in profile :
          usernames = { 'usernames': {
            'duolingo' : user['username'],
            'facebook' : profile['username']
            }
          }
          infos.update(usernames)

        if 'gender' in profile:
          gender = {'gender': profile['gender']}
          infos.update(gender)

        if 'locale' in profile:
          locale = {'locale': profile['locale']}
          infos.update(locale)

        self.socialsinfos.insert(infos)

        if counter % 20 == 0:
          print('{0} Profiles retrived by now'.format(counter))

        time.sleep(self.sleeptime)

      except StopIteration:
        print('Done!')
        break
