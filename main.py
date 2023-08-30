from urllib.parse import urlencode
import requests
from pprint import pprint
import json
from tqdm import tqdm
from time import sleep

def get_oauth_url(app_id):
    oauth_url = 'https://oauth.vk.com/authorize'
    params = {
            'client_id': app_id,
            'redirect_uri': 'https://oauth.vk.com/blank.html',
            'display': 'page',
            'scope': 'photos',
            'response_type': 'token',
            'v': 5.131
        }
    return f"{oauth_url}?{urlencode(params)}"
print(get_oauth_url('51727823'))

class UserAPIVK:
    vk_base_url = 'https://api.vk.com/method/'
    vk_token = ''

    def __init__(self, user_id):
        self.user_id = user_id
    def _getPhotos(self, amount, album):
        '''Gets certain amount photos from album'''

        params = {
            'access_token': self.vk_token,
            'owner_id': self.user_id,
            'album_id': album,
            'extended': 1,
            'count': amount,
            'v': 5.131
        }
        if self._getAlbumID(album):
            if album in ['profile', 'saved', 'wall']:
                return requests.get(f"{self.vk_base_url}photos.get?",
            params=params).json()
            else:
                params.update({'album_id': self._getAlbumID(album)})
                return requests.get(f"{self.vk_base_url}photos.get?",
                                params=params).json()
        else:
            return ''
    def _getAlbums(self):
        '''Gets information by all albums of user'''

        params = {
            'access_token': self.vk_token,
            'owner_id': self.user_id,
            'v': 5.131
        }
        return   requests.get(f"{self.vk_base_url}photos.getAlbums?{urlencode(params)}").json()

    def _getAlbumID(self, title):
        '''Gets ID of album'''

        for element_dict in self._getAlbums().get('response', '').get('items', ''):
            if element_dict.get('title', '').lower() == title.lower():
                return  element_dict.get('id', '')
            else:
                return ''


class UserAPIYA(UserAPIVK):
    ya_base_url = 'https://cloud-api.yandex.net'

    def __init__(self, user_id, ya_token):
        super().__init__(user_id)
        self.ya_token = ya_token
        self.headers = {
            'Authorization': f"OAuth {self.ya_token}",
            'Content_Type': 'application/json'
        }

    def _checkFolder(self, name_folder):
        '''checks if a folder exists on disk'''

        while True:
            params = {
                'path': name_folder
            }
            if requests.get(f"{self.ya_base_url}/v1/disk/resources", headers=self.headers,
                        params=params).status_code == 200:
                answer = input('Папка существует. Добавить фото (да/нет)?: ')
                if answer.lower() == 'да':
                    return self._createFolder(name_folder)
                else:
                    name_folder = input('Введите название папки: ')
            else:
                return self._createFolder(name_folder)


    def _createFolder(self, name_folder):
        '''create a folder by yandex drive'''

        params = {
            'path': name_folder
        }
        requests.put(f"{self.ya_base_url}/v1/disk/resources",
                                headers=self.headers,
                                params=params).json()
        return  name_folder

    def _getLinksPhotos(self, amount, album):
        '''
        Returns dict, where key is string with count of likes and key is count of likes with date of photo,
        if count of likes matches with other.
        And value is tuple from type of max_size and link of photo
        '''
        if self._getPhotos(amount, album):
            data_of_photos = self._getPhotos(amount, album).get('response', '').get('items', '')
            photos_dict = {}
            for dt_photo in tqdm(data_of_photos, desc='dt_photo', ncols=80):
                sleep(.1)
                max_size_photo = sorted(dt_photo.get('sizes', ''), key=lambda x: x.get('height', '') * x.get('width', ''))[-1]
                count_likes = str(dt_photo.get('likes', '').get('count', ''))
                date = str(dt_photo.get('date', ''))
                if count_likes in photos_dict:
                    photos_dict[f"{count_likes}_{date}"] = (max_size_photo.get('url', '') )
                else:
                    photos_dict[count_likes] = (max_size_photo.get('url', '') )
            return  photos_dict
        else:
            return ''

    def postPhoto(self, amount=5, album='profile'):
        '''
        Sends photos of user on yadisk.
        Print string 'Successfully', if request is successfully.
        Makes json-file with information of photos
        '''

        if self._getLinksPhotos(amount, album):
            name_folder = input('Введите название папки: ')
            name_folder = self._checkFolder(name_folder)
            result = []
            for key, value in tqdm(self._getLinksPhotos(amount, album).items(), desc='link', ncols=80):
                sleep(0.1)
                params = {
                'url': value[1],
                'path': f"{name_folder}/{key}.jpg"
            }
                response = requests.post(f"{self.ya_base_url}/v1/disk/resources/upload",
                                  headers = self.headers,
                                  params=params)
                if 200 < response.status_code < 300:
                    result.append({'file_name': key, 'size': value[0]})
            if result:
                with open('photos.json', 'w') as file:
                    json.dump(result , file, ensure_ascii=False, indent=2)

                    return 'Successfully'
        else:
            return 'Такого альбома не существует'



user_id = input()
ya_token = input()
user_1 = UserAPIYA(user_id, ya_token)
pprint(user_1.postPhoto())

