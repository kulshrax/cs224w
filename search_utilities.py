from collections import namedtuple

# Time bins are a tuple (start, end) denoting
# the start and end dates of a time range,
# respectively.
TimeBin = namedtuple('TimeBin', 'start end')

def posts_by_type(cursor, post_type = None):
    """
    Returns a generator of (post_id, creator_id) 
    for all posts of the given type.
    Types are as defined by StackOverflow schema.
    Types we're interested in are:
    1 - question
    2 - answer

    :param cursor: a Postgres database cursor
    :param timebin: the time bin
    """
    if post_type is None:
        post_type = 1
    query = """SELECT id, owner_user_id 
               FROM Post
               WHERE post_type_id = %(post_type)s;
            """
    cursor.execute(query, {'post_type': post_type})
    return ((result[0], result[1]) for result in cursor)

def posts_within_timebin(cursor, timebin):
    """
    Returns a generator for IDs for posts falling 
    within a time bin.

    :param cursor: a Postgres database cursor
    :param timebin: the time bin
    """
    query = """SELECT id
               FROM Post
               WHERE creation_date > %(start)s
               AND creation_date < %(end)s;
            """
    cursor.execute(query, {'start': timebin.start, 'end': timebin.end})
    return (result[0] for result in cursor)

def posts_by_user(cursor, user_id, timebin = None):
    """
    Returns a generator for IDs for posts made by a
    given user. Optionally filter by the given 
    timebin.

    :param cursor: a Postgres database cursor
    :param user_id: the user id
    :param timebin: timebin to filter posts.
    """
    if timebin is None:
        query = """SELECT id
                   FROM Post
                   WHERE owner_user_id = %(user_id)s;
                """
        cursor.execute(query, {'user_id': user_id})
    else:
        query = """SELECT id
                   FROM Post
                   WHERE owner_user_id = %(user_id)s
                   AND creation_date > %(start)s
                   AND creation_date < %(end)s;
                """
        cursor.execute(query, {'user_id': user_id, 'start': timebin.start, 'end': timebin.end})
    return (result[0] for result in cursor)

def users_above_threshold(cursor, threshold):
    """
    Returns a generator for IDs for users with 
    reputation above a threshold.

    :param cursor: a Postgres database cursor
    :param threshold: the reputation threshold
    """
    query = """SELECT id
               FROM se_user
               WHERE reputation > %(threshold)s;
            """
    cursor.execute(query, {'threshold': threshold})
    return (result[0] for result in cursor)

def users_in_post(cursor, post_id, timebin = None):
    """
    Returns a generator for IDs for users who 
    answered a post given by id. Optionally filter
    by users who answered within a given timebin.

    :param cursor: a Postgres database cursor
    :param post_id: the post id
    """
    if timebin is None:
        query = """SELECT DISTINCT t1.owner_user_id
                   FROM Post t1
                   INNER JOIN Post t2
                   ON t1.parent_id = t2.id
                   WHERE t1.post_type_id = 2 
                   AND t2.post_type_id = 1 
                   AND t2.id = %(post_id)s;
                """
        cursor.execute(query, {'post_id': post_id})
    else:
        query = """SELECT DISTINCT t1.owner_user_id
                   FROM Post t1
                   INNER JOIN Post t2
                   ON t1.parent_id = t2.id
                   WHERE t1.post_type_id = 2 
                   AND t2.post_type_id = 1 
                   AND t2.id = %(post_id)s
                   AND t1.creation_date > %(start)s
                   AND t1.creation_date < %(end)s;
                """
        cursor.execute(query, {'post_id': post_id, 'start': timebin.start, 'end': timebin.end})
    return (result[0] for result in cursor)

def users_by_tournament(cursor, timebin = None):
    """
    Returns a generator for 
    ((user_id, score), (user_id, score)) 
    pairs where both users post an answer the same 
    question.  Optionally considers only posts made 
    within a given time bin.

    Results are ordered by the date of the later
    post in the pair since that is when the
    tournament occurs.

    For use with ELO calculation.
    """
    if timebin is None:
        query = """SELECT u1.id, a1.score, u2.id, a2.score
                   FROM Post q
                   INNER JOIN Post a1
                   ON q.id = a1.parent_id
                   INNER JOIN Post a2
                   ON q.id = a2.parent_id
                   INNER JOIN se_user u1
                   ON u1.id = a1.owner_user_id
                   INNER JOIN se_user u2
                   ON u2.id = a2.owner_user_id
                   ORDER BY GREATEST(a1.creation_date, a2.creation_date);
                """
        cursor.execute(query)
    else:
        query = """SELECT u1.id, a1.score, u2.id, a2.score
                   FROM Post q
                   INNER JOIN Post a1
                   ON q.id = a1.parent_id
                   INNER JOIN Post a2
                   ON q.id = a2.parent_id
                   INNER JOIN se_user u1
                   ON u1.id = a1.owner_user_id
                   INNER JOIN se_user u2
                   ON u2.id = a2.owner_user_id
                   WHERE a1.creation_date > %(start)s
                   AND a1.creation_date < %(end)s
                   AND a2.creation_date > %(start)s
                   AND a2.creation_date < %(end)s
                   ORDER BY GREATEST(a1.creation_date, a2.creation_date);
                """
        cursor.execute(query, {'start': timebin.start, 'end': timebin.end})
    return (((result[0], result[1]), (result[2], result[3])) for result in cursor)

def cau(cursor, user_id, timebin = None):
    """
    Returns the cumulative aggregate upvote score for
    a user. By default this returns the score over the
    entire dataset. Optionally specify a timebin to
    compute the cau score within a specific time interval.
    """
    if timebin is None:
        query = """SELECT SUM(score) FROM Post
                   WHERE owner_user_id = %(user_id)s
                   AND post_type_id = 2
                """
        cursor.execute(query, {'user_id': user_id})
    else:
        query = """SELECT SUM(score) FROM Post
                   WHERE owner_user_id = %(user_id)s
                   AND post_type_id = 2
                   AND creation_date > %(start)s
                   AND creation_date < %(end)s;
                """
        cursor.execute(query, {'user_id': post_id, 'start': timebin.start, 'end': timebin.end})
    return cur.fetchone()