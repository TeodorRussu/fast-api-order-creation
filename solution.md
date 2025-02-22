# **Solution Document**

## **Approach**

### **Order Placement Process**:

When an order request is received the following steps are executed:
create an OrderEntity object with all the details received in the request + a column 'status'

#### Database Order table structure:

```
    id          varchar           not null,
    created_at  timestamp,
    type        varchar           not null,
    side        varchar           not null,
    instrument  varchar           not null,
    limit_price double precision,
    quantity    integer           not null,
    status      order_status_enum not null,
    
    primary key (id, status)`
```

**If the request is valid, the following steps are performed:**

1. insert one **Order** record in the database with status = INITIATED
2. post the order to the exchange
3. insert one **Order** record in the database with status COMPLETED

If everything is executed successfully, the database should contain 2 records for the same order(INITIATED, COMPLETED).
**The request will return the code 201**.

**What will be stored in the database for some commonly expected scenarios:**

### **Happy flow**:

1. insert one order record in the database with status = INITIATED -> success
2. post the order to the exchange -> success
3. insert one order record in the database with status COMPLETED. -> success

**Expected records in the database:**
Order(id..., status = INITIATED)
Order(id..., status = EXCHANGE_CREATION_FAILED)

### Error flows

In case step 1, 2 or 3 fails, using exception handling another record will be inserted in the database with the same
uuid, and status EXCHANGE_CREATION_FAILED or DATABASE_PERSISTENCE_FAILED
and the request is considered as failed, **and will return the error 500**.

Potential failiing scenarios:

Failing Case 1. Most expected failing scenario:

```
1. insert one order record in the database with status = INITIATED                   -> success
2. post the order to the exchange                                                    -> failure 
3. insert one order record in the database with status EXCHANGE_CREATION_FAILED.     -> success

Expected records in the database:
Order(id..., status = INITIATED)
Order(id..., status = EXCHANGE_CREATION_FAILED)
```

Other failure cases can occur when there are database issues (e.g database connection failures) are less likely, but
they will be hadled accordingly:
Failing Case 2:

```
1. insert one order record in the database with status = INITIATED                   -> success
2. post the order to the exchange                                                    -> success
3. insert one order record in the database with status COMPLETED                     -> failed
4. insert one order record in the database with status DATABASE_PERSISTENCE_FAILED.  -> success

Expected records in the database:
Order(id..., status = INITIATED)
Order(id..., status = DATABASE_PERSISTENCE_FAILED)
```

Failing Case 3:

```
1. insert one order record in the database with status = INITIATED                   -> failure
2. post the order to the exchange                                                    -> skip
3. insert one order record in the database with status COMPLETED                     -> skip
4. insert one order record in the database with status DATABASE_PERSISTENCE_FAILED.  -> success

Expected records in the database:
Order(id..., status = INITIATED)
Order(id..., status = DATABASE_PERSISTENCE_FAILED)
```

There are some other potential failure scenarios.

To run the application locally, it is required:

* python 3.9 or newer
* docker and docker-compose

before starting the FastAPI application the database should be started using docker-compose

```
docker-compose up
```

once the database is up and running, the app can be started with:

```
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

When application started, a post request needs to be sent in order to trigger the functionality:

```
curl --location 'http://127.0.0.1:8000/orders' \
--header 'Content-Type: application/json' \
--data '{
    "type": "limit",
    "side": "buy",
    "instrument": "AAPL12345678",
    "limit_price": 150.00,
    "quantity": 10
}'
```

### Testing.

Functional test have been added for the scenarios highlighted above

Other tests that should be added:

* integration tests for the POST endpoint to validate the correct response in happy/unhappy flows
* integration tests for the input validation
* unit tests for the mappers

### Improvements and Future Enhancements

While the current approach provides a good base for processing orders, there are several improvements that should be
incorporated to make the system more robust and scalable and as much as possible self-healing. A few ideas:

#### - Retry and Reconciliation Mechanism

Currently, the application handle immediate failures by logging them and raising HTTP exceptions. However, for better
reliability, a good idea would be to add a reconciliation task/job.
This task should run on a schedule and attempt to retry failed orders by checking if the order has been successfully
placed in the exchange or database.
This will help to ensure that failed orders are eventually processed without requiring manual intervention.

#### - Order Verification from Exchange

To improve the reliability of the exchange order placement system, it is also required a query function for the order
status in the stock_exchange client.
This function should be able query the exchange service to verify whether an order was placed or not. The reconciliation
job can use this verification to determine if an order needs to be retried or if it should be marked as successfully
processed.

#### - Add observability for the Order Service and set alerts for the error scenarios.

### Bonus Question:

How would you change the system if we would receive a high volume of async updates to the orders placed through a socket
connection on the stock exchange, e.g. execution information?

### Answer

A queue-based architecture (such as SQS) would allow decoupling order creation from immediate processing. Orders could
be placed in a queue, which is then processed asynchronously by worker services.
This architecture allows us to scale the system to handle higher volumes of orders without impacting performance.

For example the service responsibilities can be split between:

1. a socket client that will just receive notifications, and publish them to a queue
2. a processor scaled horisontally according to the load, which will process the order requests asynchronously

Another point is that in case of a big load, request throttling can happen on the Exchange Service. To handle this, a
circuit breaking mechanism can be considered.

### Disclaimer
As a full time Java/Kotlin engineer, this being my first project in FastAPI, I admit that there might be room for significant improvements regarding the best practices used in python and FastAPI.