import requests, pymongo, time, json, random


class Crawlingo:

  def __init__(self):

    self.api  = {
      'host': "https://www.duolingo.com",
      'resources': {
        'friendships' : 'friendships',
        'userinfo' : 'users'
      }
    }

    self.visited = set()
    self.sleeptime = 0.5

    connection = pymongo.Connection()
    self.db = connection['duolingo']
    self.friendships = self.db['friendships']

    self.users = self.db['users']
    self.logs = self.db['logs']


  def request(self, resource, param = None):
    return self.api['host'] + '/' + self.api['resources'][resource] + (param and '/' + str(param)) or ('')


  def getResource(self, resource, param):
    response = None
    backoff = 20
    while response == None and backoff <= 160 :
      try:
        response = json.loads(requests.get(self.request(resource,param)).text)
      except Exception:
        print("Somenthing went wront with the requests, retrying in {1} seconds. Failed request: {0} ".format(self.request(resource,param),backoff))
        backoff *= 2
        continue

    if response == None:
      print("Skipping this request".format(self.request(resource,param)))

    return response




  def getFriendship(self,id):
    data = self.getResource('friendships',id)
    followers = { str(follower['id']): follower['username'] for follower in data['followers'] }
    following = { str(follower['id']): follower['username'] for follower in data['following'] }
    return { 'followers' : followers, 'following' : following }

  def getInfo(self, username):
    data = self.getResource('userinfo', username)
    return data

  def getProfilesInfo(self):
    stored = self.logs.find({},{'status':0})
    visited_ids = [s['_id'] for s in list(stored)]
    users = self.friendships.find({'_id': {'$nin': visited_ids}},{'friendships':0})
    for user in list(users):
      print("Getting profile of {0}".format(user['username']))

      data = self.getInfo(user['username'])

      self.visited.add(int(user['_id']))

      if data == None:
        log = {'_id' : user['_id'], 'status': False}
        self.logs.insert(log)
        continue


      user_data = {
        '_id' : user['_id'],
        'username': data['username'],
        'fullname': data['fullname'],
        'social_ids': {
          'facebook'  : data['facebook_id'],
          'twitter'   : data['twitter_id'],
          'gplus'     : data['gplus_id']
        }
      }

      if 'languages' in data:
        lang = { 'languages': {
          'data': data['languages'],
          'browser_language': data['browser_language'],
          'ui_language': data['ui_language'],
          'learning': data['learning_language_string']
          }
        }
        user_data.update(lang)

      log = {'_id' : user['_id'], 'status': True}
      self.users.insert(user_data)
      self.logs.insert(log)

      if len(self.visited) % 20 == 0 :
        print("{0} nodes visited.".format(len(self.visited)))
        failed_visit = len(list(self.db['logs'].find({'status': False})))
        print("Failed {0}".format(failed_visit))

      #fuzz = random.random() - 0.3
      time.sleep(self.sleeptime)  # [0.5,1.5] average waiting time : ~1sec


  def crawl(self,seed_id, max_depth, seed_name = None):

    friendships_data = self.getFriendship(seed_id)

    friendship = {
        '_id' : seed_id,
        'username' : seed_name,
        'friendships' : friendships_data
    }

    self.friendships.insert(friendship)

    depth = 1
    while depth < max_depth:
      print("We enter depth {0}".format(depth))
      depth += 1
      (queue, friendships_data) = (friendships_data, {'followers':{}, 'following': {}})
      for fid,username in dict(list(queue['followers'].items()) + list(queue['following'].items())).items():

        if int(fid) in self.visited:
          print('Already visited node, id: ' + fid)
          continue

        # Naive exp backoff, bounce node after some attempts
        try:
          tmp_friendships_data = self.getFriendship(fid)
        except Exception :
          print("Somenthing went wront with the requests, on userd id {0} ".format(fid))
          tmp_friendships_data = None
          backoff = 20
          while tmp_friendships_data == None and backoff <= 160 :
            print("Trying again in {0} seconds".format(backoff))
            time.sleep(backoff)
            try:
              tmp_friendships_data = self.getFriendship(fid)
            except Exception:
              print("Somenthing went wront with the requests, on userd id {0} ".format(fid))
              backoff *= 2
              continue
          if tmp_friendships_data == None:
            print("Skipping this one, going on...")
            continue
          print("Finally worked, going on now ...")


        friendship = {
          '_id' : int(fid),
          'username' : username,
          'friendships' : tmp_friendships_data
        }

        self.friendships.insert(friendship)
        self.visited.add(int(fid))

        if len(self.visited) % 10 == 0 :
          print("{0} nodes visited.".format(len(self.visited)))

        friendships_data['followers'].update(tmp_friendships_data['followers'])
        friendships_data['following'].update(tmp_friendships_data['following'])

        fuzz = random.random() - 0.3
        time.sleep(self.sleeptime + fuzz )  # [0.5,1.5] average waiting time : ~1sec






