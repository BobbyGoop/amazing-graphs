from sqlalchemy.exc import IntegrityError
from flask import redirect, url_for, request
from flask_restful import Resource, reqparse
from db_models import *
from db_setup import db_session


class ClientWrapper(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('client_id', type=int, help="Enter the client id")
        self.parser.add_argument('client_name', type=str, help="Enter the client name")
        self.parser.add_argument('client_surname', type=str, help="Enter the client surname")
        self.parser.add_argument('client_email', type=str, help="Enter the client email")

    @classmethod
    def validate_data(cls, data):
        # Если не передано значение
        if not data:
            return None
        # Если переданы неправильные атрибуты
        if not (set(data.keys()) <= set(Client.__table__.columns.keys())):
            return None
        return data

    # Only PARAMS
    def get(self):
        _id = self.parser.parse_args().get('client_id')

        return db_session.query(Client).get(_id).serialize() if _id else \
            list(map(lambda cl: cl.serialize(), db_session.query(Client).all()))

    def post(self):
        _name = self.parser.parse_args().get('client_name')
        _surname = self.parser.parse_args().get('client_surname')
        _email = self.parser.parse_args().get('client_email')
        if _name and _surname and _email:
            try:
                c = Client(_name, _surname, _email)
                db_session.add(c)
                db_session.flush()
                db_session.add(Order(c.id, c.name, 0))
                db_session.commit()
                print("Добавлено")
                return redirect(url_for('register'))
            except IntegrityError:
                db_session.rollback()
                return {"message": "Email is already registered"}, 400
        elif request.content_type == 'application/json':
            data = self.validate_data(request.get_json(force=True))
            if not data:
                return {"message": "Bad request"}, 400
            if list(data.keys()) != ["name", "surname", "email"]:
                return {"message": "Bad request"}, 400
            try:
                db_session.add(Client(data["name"], data["surname"], data["email"]))
                db_session.commit()
            except IntegrityError:
                db_session.rollback()
                return {"message": "Bad request"}, 400
        else:
            # db_session.rollback()
            print("Ошибка добавления в БД")
            return None, 400

    # Only JSON
    def patch(self):
        if request.content_type != 'application/json':
            return {"message": "Invalid content type"}, 400
        data = self.validate_data(request.get_json(force=True))
        try:
            if data['id'] is None:
                raise TypeError
            client = db_session.query(Client).get(data['id'])
            attributes = list(data.keys())
            for attr in attributes[1:]:
                setattr(client, attr, data[attr])
                db_session.flush()
            db_session.commit()
        except (TypeError, AttributeError, IntegrityError):
            db_session.rollback()
            return {"message": "Wrong params"}, 400

    # Only PARAMS
    def delete(self):
        _id = self.parser.parse_args().get('client_id')
        if _id:
            client = db_session.query(Client).get(_id)
            print(client)
            if client:
                db_session.delete(client)
                db_session.commit()
            else:
                return {"message": "Client not found"}, 400
        else:
            return None, 400


class OrderWrapper(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('order_id', type=int)
        self.parser.add_argument('total', type=int)
        self.parser.add_argument('client_id', type=int)

    def get(self):
        _cid = self.parser.parse_args().get('client_id')
        _id = self.parser.parse_args().get('order_id')
        if not _cid and not _id:
            return {'orders': list(map(lambda cl: cl.serialize(), Order.query.all()))}
        elif _cid and _id:
            ordr = db_session.query(Order).get(_id)
            if ordr and (ordr.client_id == _cid):
                return ordr.serialize(), 200
            else:
                return None, 404
        elif _cid and not _id:
            return list(map(lambda o: o.serialize(), filter(lambda o: o.client_id == _cid, db_session.query(Order).all())))

    def post(self):
        _cid = self.parser.parse_args().get('client_id')
        _total = self.parser.parse_args().get('total')
        try:
            c = db_session.query(Client).get(_cid)
            db_session.add(Order(c.id, c.name, _total))
            db_session.commit()
            print("Добавлено")
        except AttributeError:
            db_session.rollback()
            print("Ошибка добавления в БД")
            return None, 400

    def patch(self):
        pass

    def delete(self):
        pass
