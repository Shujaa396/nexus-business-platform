import sys
from sqlalchemy import create_engine
sys.path.append(r'c:\Users\DELL\Desktop\nexus-business-platform\backend')
from app.models import Base

def main():
    engine = create_engine('sqlite:///./test.db')
    Base.metadata.create_all(engine)
    print('created')

if __name__ == '__main__':
    main()
