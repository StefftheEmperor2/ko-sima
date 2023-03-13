import re

class ComplexFilter:
    OPERATOR_AND = 'and'
    OPERATOR_OR = 'or'

    def __init__(self):
        self.operator = 'and'
        self.compounds = []

    def set_operator_and(self):
        self.operator = self.OPERATOR_AND
        return self

    def set_operator_or(self):
        self.operator = self.OPERATOR_OR
        return self

    def add_compound(self, compound):
        self.compounds.append(compound)
        return self

    def get_payload(self):
        compounds = []
        for compound in self.compounds:
            compounds.append(compound.get_payload())
        return {
            self.operator: compounds
        }

    def has_filter(self):
        if len(self.compounds) == 0:
            return False
        for compound in self.compounds:
            if isinstance(compound, SimpleFilter):
                return True
            if isinstance(compound, ComplexFilter):
                return compound.has_filter()
        return False

    def __len__(self):
        return len(self.compounds)


class SimpleFilter:
    OPERATOR_IS = 'is'
    OPERATOR_IS_NOT = 'isnot'
    OPERATOR_CONTAINS = 'contains'

    def __init__(self, field, operator, value):
        self.field = field
        self.operator = operator
        self.value = value

    def get_payload(self):
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value
        }


class FilterParser:
    ARTIST_FIELDS = [
        'MUSICBRAINZ_ARTISTID',
        'Genre',
        'artist',
        'albumartist',
        'album'
    ]

    ALBUM_FIELDS = [
        'MUSICBRAINZ_ARTISTID',
        'musicbrainz_albumartistid',
        'Genre',
        'artist',
        'albumartist',
        'album'
    ]

    SONG_FIELDS = [
        'MUSICBRAINZ_ARTISTID',
        'Genre',
        'artist',
        'albumartist',
        'album'
    ]

    KODI_SUPPORTED_ARTIST_FIELDS = [
        'Genre',
        'artist'
    ]

    KODI_SUPPORTED_ALBUM_FIELDS = [
        'Genre',
        'artist',
        'albumartist',
        'album'
    ]

    KODI_SUPPORTED_SONG_FIELDS = [
        'Genre',
        'artist',
        'albumartist',
        'album'
    ]

    KODI_ARTIST_FIELD_MAPPINGS = [
        ('Genre', 'genre'),
        ('artist', 'artist')
    ]

    KODI_ALBUM_FIELD_MAPPINGS = [
        ('Genre', 'genre'),
        ('artist', 'artist'),
        ('albumartist', 'artist'),
        ('album', 'album')
    ]

    KODI_SONG_FIELD_MAPPINGS = [
        ('Genre', 'genre'),
        ('artist', 'artist'),
        ('albumartist', 'albumartist'),
        ('album', 'album')
    ]

    OPERATORS = [
        ('==', 'is'),
        ('!=', 'isnot')
    ]

    ARTIST_FIELD_MAPPINGS = [
        ('musicbrainzartistid', 'MUSICBRAINZ_ARTISTID'),
        ('genre', 'Genre'),
        ('artist', 'artist'),
        ('albumartist', 'albumartist')
    ]

    ALBUM_FIELD_MAPPINGS = [
        ('musicbrainzartistid', 'MUSICBRAINZ_ARTISTID'),
        ('musicbrainzalbumartistid', 'musicbrainz_albumartistid'),
        ('genre', 'Genre'),
        ('artist', 'artist'),
        ('artist', 'albumartist'),
        ('title', 'album')
    ]

    SONG_FIELD_MAPPINGS = [
        ('musicbrainzartistid', 'MUSICBRAINZ_ARTISTID'),
        ('genre', 'Genre'),
        ('artist', 'artist'),
        ('artist', 'albumartist'),
        ('album', 'album'),
        ('title', 'track')
    ]

    UNPACKING_NEEDING_ARTIST_FIELDS = [
        'musicbrainzartistid',
        'genre',
        'albumartist'
    ]

    UNPACKING_NEEDING_ALBUM_FIELDS = [
        'musicbrainzartistid',
        'musicbrainzalbumartistid',
        'genre',
        'artist'
    ]

    UNPACKING_NEEDING_SONG_FIELDS = [
        'musicbrainzartistid',
        'musicbrainzalbumartistid',
        'genre',
        'artist',
        'albumartist'
    ]

    SECTION_ALBUMS = 'albums'
    SECTION_ARTISTS = 'artists'
    SECTION_SONGS = 'songs'

    def __init__(self, filter_string):
        self.filter_string = filter_string

    def get_filter(self, section):
        native_operators = [o[0] for o in self.OPERATORS]
        if section == self.SECTION_ALBUMS:
            fields = self.ALBUM_FIELDS
        elif section == self.SECTION_ARTISTS:
            fields = self.ARTIST_FIELDS
        elif section == self.SECTION_SONGS:
            fields = self.SONG_FIELDS
        else:
            raise SectionError(section)

        regex = re.compile(
            f'^(\\s*{"|".join(fields)}\\s*) ({"|".join(native_operators)}) '
            f'(?P<quote>[\'"])([a-zA-Z0-9_&\\[\\]\\-\\s]*)(?P=quote)$')
        matches = regex.match(self.filter_string)
        if matches:
            return SimpleFilter(matches[1], self.find_kodi_operator(matches[2]), matches[3])

        regex = re.compile(
            f'^\\(\\s*({"|".join(fields)}) ({"|".join(native_operators)}) '
            '(?P<quote>[\'"])([a-zA-Z0-9_&\\[\\]\\-\\s]*)(?P=quote)\\)$')
        matches = regex.match(self.filter_string)
        if matches:
            return SimpleFilter(matches[1], self.find_kodi_operator(matches[2]), matches[4])

        regex = re.compile(
            f'^(?P<open_para>[(]?)([a-zA-Z0-9()=!_&\\-\'"\\s]*) (AND|OR) '
            f'([a-zA-Z0-9()=!_\\[\\]\\-\'"\\s]*)(?(open_para)[)])$')
        matches = regex.match(self.filter_string)
        if matches:
            complex_filter = ComplexFilter()
            complex_filter.operator = matches[3].lower()
            complex_filter.add_compound(FilterParser(matches[2]).get_filter(section))
            complex_filter.add_compound(FilterParser(matches[4]).get_filter(section))
            return complex_filter

        return None

    def get_kodi_filter_of_filter(self, section, raw_filter):
        if section == self.SECTION_ALBUMS:
            fields = self.KODI_SUPPORTED_ALBUM_FIELDS
        elif section == self.SECTION_ARTISTS:
            fields = self.KODI_SUPPORTED_ARTIST_FIELDS
        elif section == self.SECTION_SONGS:
            fields = self.KODI_SUPPORTED_SONG_FIELDS
        else:
            raise SectionError(section)
        if isinstance(raw_filter, SimpleFilter) and raw_filter.field in fields:
            return SimpleFilter(self.find_kodi_field(section, raw_filter.field), raw_filter.operator, raw_filter.value)
        if isinstance(raw_filter, ComplexFilter):
            kodi_filter = ComplexFilter()
            kodi_filter.operator = raw_filter.operator
            for compound in raw_filter.compounds:
                compound_kodi_filter = self.get_kodi_filter_of_filter(section, compound)
                if compound_kodi_filter:
                    kodi_filter.add_compound(compound_kodi_filter)
            return kodi_filter
        return None

    def get_kodi_filter(self, section):
        raw_filter = self.get_filter(section)
        return self.get_kodi_filter_of_filter(section, raw_filter)

    def find_kodi_operator(self, native_operator):
        for op in self.OPERATORS:
            if op[0] == native_operator:
                return op[1]
        return None

    def find_kodi_field(self, section, native_field):
        if section == self.SECTION_ALBUMS:
            mapping = self.KODI_ALBUM_FIELD_MAPPINGS
        elif section == self.SECTION_ARTISTS:
            mapping = self.KODI_ARTIST_FIELD_MAPPINGS
        elif section == self.SECTION_SONGS:
            mapping = self.KODI_SONG_FIELD_MAPPINGS
        else:
            raise SectionError(section)
        for kodi_field_mapping in mapping:
            if kodi_field_mapping[0] == native_field:
                return kodi_field_mapping[1]
        return None

    def get_artist_data_field(self, field_name):
        for kodi_field, native_field in self.ARTIST_FIELD_MAPPINGS:
            if native_field == field_name:
                return kodi_field
        return None

    def get_album_data_field(self, field_name):
        for kodi_field, native_field in self.ALBUM_FIELD_MAPPINGS:
            if native_field == field_name:
                return kodi_field
        return None

    def get_song_data_field(self, field_name):
        for kodi_field, native_field in self.SONG_FIELD_MAPPINGS:
            if native_field == field_name:
                return kodi_field
        return None

    def artist_data_matches_filter(self, artist_data, current_filter):
        if isinstance(current_filter, SimpleFilter):
            artist_data_field = self.get_artist_data_field(current_filter.field)
            if not artist_data_field:
                raise ArtistFieldUnsupportedException(current_filter.field)
            if artist_data_field in self.UNPACKING_NEEDING_ARTIST_FIELDS:
                artist_field_value = next(iter(artist_data[artist_data_field] or []), None)
            else:
                artist_field_value = artist_data[artist_data_field]
            if current_filter.operator == SimpleFilter.OPERATOR_IS:
                if artist_data_field == 'genre':
                    return artist_field_value == current_filter.value \
                           or current_filter.value in [g['title'] for g in artist_data['songgenres']]
                return artist_field_value == current_filter.value
            if current_filter.operator == SimpleFilter.OPERATOR_IS_NOT:
                if artist_data_field == 'genre':
                    return artist_field_value != current_filter.value \
                           and current_filter.value not in [g['title'] for g in artist_data['songgenres']]
                return artist_field_value != current_filter.value
        if isinstance(current_filter, ComplexFilter):
            if current_filter.operator == ComplexFilter.OPERATOR_AND:
                for compound in current_filter.compounds:
                    if not self.artist_data_matches_filter(artist_data, compound):
                        return False
                return True
            if current_filter.operator == ComplexFilter.OPERATOR_OR:
                for compound in current_filter.compounds:
                    if self.artist_data_matches_filter(artist_data, compound):
                        return True
                return False

    def album_data_matches_filter(self, album_data, current_filter):
        if isinstance(current_filter, SimpleFilter):
            album_data_field = self.get_album_data_field(current_filter.field)
            if not album_data_field:
                raise AlbumFieldUnsupportedException(current_filter.field)
            if album_data_field in self.UNPACKING_NEEDING_ALBUM_FIELDS:
                album_field_value = next(iter(album_data[album_data_field] or []), None)
            else:
                album_field_value = album_data[album_data_field]
            if current_filter.operator == SimpleFilter.OPERATOR_IS:
                return album_field_value == current_filter.value
            if current_filter.operator == SimpleFilter.OPERATOR_IS_NOT:
                return album_field_value != current_filter.value
        if isinstance(current_filter, ComplexFilter):
            if current_filter.operator == ComplexFilter.OPERATOR_AND:
                for compound in current_filter.compounds:
                    if not self.album_data_matches_filter(album_data, compound):
                        return False
                return True
            if current_filter.operator == ComplexFilter.OPERATOR_OR:
                for compound in current_filter.compounds:
                    if self.album_data_matches_filter(album_data, compound):
                        return True
                return False

    def song_data_matches_filter(self, song_data, current_filter):
        if isinstance(current_filter, SimpleFilter):
            song_data_field = self.get_song_data_field(current_filter.field)
            if not song_data_field:
                raise ArtistFieldUnsupportedException(current_filter.field)
            if song_data_field in self.UNPACKING_NEEDING_SONG_FIELDS:
                song_field_value = next(iter(song_data[song_data_field] or []), None)
            else:
                song_field_value = song_data[song_data_field]
            if current_filter.operator == SimpleFilter.OPERATOR_IS:
                if song_data_field == 'genre':
                    return song_field_value == current_filter.value \
                           or current_filter.value in [g['title'] for g in song_data['songgenres']]
                return song_field_value == current_filter.value
            if current_filter.operator == SimpleFilter.OPERATOR_IS_NOT:
                if song_field_value == 'genre':
                    return song_field_value != current_filter.value \
                           and current_filter.value not in [g['title'] for g in song_data['songgenres']]
                return song_field_value != current_filter.value
        if isinstance(current_filter, ComplexFilter):
            if current_filter.operator == ComplexFilter.OPERATOR_AND:
                for compound in current_filter.compounds:
                    if not self.song_data_matches_filter(song_data, compound):
                        return False
                return True
            if current_filter.operator == ComplexFilter.OPERATOR_OR:
                for compound in current_filter.compounds:
                    if self.song_data_matches_filter(song_data, compound):
                        return True
                return False

    def matches_artist_data(self, artist_data):
        current_filter = self.get_filter(self.SECTION_ARTISTS)
        return self.artist_data_matches_filter(artist_data, current_filter)

    def matches_album_data(self, album_data):
        current_filter = self.get_filter(self.SECTION_ALBUMS)
        return self.album_data_matches_filter(album_data, current_filter)

    def matches_song_data(self, artist_data):
        current_filter = self.get_filter(self.SECTION_SONGS)
        return self.song_data_matches_filter(artist_data, current_filter)


class ArtistFieldUnsupportedException(BaseException):
    pass


class AlbumFieldUnsupportedException(BaseException):
    pass


class SectionError(BaseException):
    pass
