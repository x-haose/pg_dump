FROM rabbitmq:3.11.5-management

RUN set eux; \
    rabbitmq-plugins enable --offline rabbitmq_stomp; \
    rabbitmq-plugins enable --offline rabbitmq_web_stomp;

EXPOSE 15671 15672 15674 61613
