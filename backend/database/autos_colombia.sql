--
-- PostgreSQL database dump
--

\restrict 3OOIa7dgMG9tEvjWDSowB60cw7mjehCluHnebZnQR7ewY2vbgUag8EZZB5kjTLp

-- Dumped from database version 16.16 (Debian 16.16-1.pgdg13+1)
-- Dumped by pg_dump version 16.16 (Debian 16.16-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: celda; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.celda (
    id bigint NOT NULL,
    codigo text NOT NULL,
    tipo text NOT NULL,
    CONSTRAINT ck_celda_codigo_no_vacio CHECK ((codigo ~ '[^[:space:]]'::text)),
    CONSTRAINT ck_celda_codigo_normalizado CHECK ((codigo = upper(regexp_replace(codigo, '^[[:space:]]+|[[:space:]]+$'::text, ''::text, 'g'::text)))),
    CONSTRAINT ck_celda_tipo_no_vacio CHECK ((tipo ~ '[^[:space:]]'::text))
);


--
-- Name: celda_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.celda ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.celda_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: cliente; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cliente (
    id bigint NOT NULL,
    nombre text NOT NULL,
    documento text NOT NULL,
    telefono text NOT NULL,
    CONSTRAINT ck_cliente_documento_no_vacio CHECK ((documento ~ '[^[:space:]]'::text)),
    CONSTRAINT ck_cliente_nombre_no_vacio CHECK ((nombre ~ '[^[:space:]]'::text)),
    CONSTRAINT ck_cliente_telefono_no_vacio CHECK ((telefono ~ '[^[:space:]]'::text))
);


--
-- Name: cliente_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.cliente ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.cliente_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: estancia; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.estancia (
    id bigint NOT NULL,
    vehiculo_id bigint NOT NULL,
    celda_id bigint NOT NULL,
    entrada timestamp with time zone DEFAULT now() NOT NULL,
    salida timestamp with time zone,
    operador_entrada_id bigint NOT NULL,
    operador_salida_id bigint,
    CONSTRAINT ck_estancia_cierre_completo CHECK (((salida IS NULL) = (operador_salida_id IS NULL))),
    CONSTRAINT ck_estancia_orden_fechas CHECK ((salida >= entrada))
);


--
-- Name: estancia_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.estancia ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.estancia_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: operador; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.operador (
    id bigint NOT NULL,
    nombre text NOT NULL,
    telefono text NOT NULL,
    usuario text NOT NULL,
    password_hash text NOT NULL,
    turno text NOT NULL,
    rol text NOT NULL,
    CONSTRAINT ck_operador_nombre_no_vacio CHECK ((nombre ~ '[^[:space:]]'::text)),
    CONSTRAINT ck_operador_password_hash_no_vacio CHECK ((password_hash ~ '[^[:space:]]'::text)),
    CONSTRAINT ck_operador_rol CHECK ((rol = ANY (ARRAY['ADMINISTRADOR'::text, 'OPERADOR'::text]))),
    CONSTRAINT ck_operador_telefono_no_vacio CHECK ((telefono ~ '[^[:space:]]'::text)),
    CONSTRAINT ck_operador_turno CHECK ((turno = ANY (ARRAY['DIA'::text, 'NOCHE'::text]))),
    CONSTRAINT ck_operador_usuario_no_vacio CHECK ((usuario ~ '[^[:space:]]'::text))
);


--
-- Name: operador_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.operador ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.operador_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: pago; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pago (
    id bigint NOT NULL,
    vehiculo_id bigint NOT NULL,
    operador_id bigint NOT NULL,
    monto numeric(10,2) NOT NULL,
    periodo_inicio date NOT NULL,
    periodo_fin date NOT NULL,
    fecha_pago timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_pago_monto_positivo CHECK ((monto > (0)::numeric)),
    CONSTRAINT ck_pago_periodo_orden CHECK ((periodo_fin >= periodo_inicio))
);


--
-- Name: pago_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.pago ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.pago_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: token_revocado; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.token_revocado (
    jti text NOT NULL,
    expira timestamp with time zone NOT NULL
);


--
-- Name: vehiculo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vehiculo (
    id bigint NOT NULL,
    placa text NOT NULL,
    color text NOT NULL,
    modelo integer NOT NULL,
    marca text NOT NULL,
    tipo text NOT NULL,
    cliente_id bigint NOT NULL,
    CONSTRAINT ck_vehiculo_color_no_vacio CHECK ((color ~ '[^[:space:]]'::text)),
    CONSTRAINT ck_vehiculo_marca_no_vacia CHECK ((marca ~ '[^[:space:]]'::text)),
    CONSTRAINT ck_vehiculo_modelo_anio CHECK (((modelo >= 1900) AND (modelo <= 2200))),
    CONSTRAINT ck_vehiculo_placa_no_vacia CHECK ((placa ~ '[^[:space:]]'::text)),
    CONSTRAINT ck_vehiculo_placa_normalizada CHECK ((placa = upper(regexp_replace(placa, '^[[:space:]]+|[[:space:]]+$'::text, ''::text, 'g'::text)))),
    CONSTRAINT ck_vehiculo_tipo CHECK ((tipo = ANY (ARRAY['MOTO'::text, 'AUTOMOVIL'::text, 'CAMIONETA'::text])))
);


--
-- Name: vehiculo_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.vehiculo ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.vehiculo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.alembic_version VALUES ('0005');


--
-- Data for Name: celda; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (1, 'MOTO-01', 'MOTO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (2, 'MOTO-02', 'MOTO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (3, 'MOTO-03', 'MOTO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (4, 'MOTO-04', 'MOTO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (5, 'MOTO-05', 'MOTO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (6, 'MOTO-06', 'MOTO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (7, 'MOTO-07', 'MOTO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (8, 'MOTO-08', 'MOTO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (9, 'MOTO-09', 'MOTO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (10, 'MOTO-10', 'MOTO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (11, 'CARRO-001', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (12, 'CARRO-002', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (13, 'CARRO-003', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (14, 'CARRO-004', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (15, 'CARRO-005', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (16, 'CARRO-006', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (17, 'CARRO-007', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (18, 'CARRO-008', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (19, 'CARRO-009', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (20, 'CARRO-010', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (21, 'CARRO-011', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (22, 'CARRO-012', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (23, 'CARRO-013', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (24, 'CARRO-014', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (25, 'CARRO-015', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (26, 'CARRO-016', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (27, 'CARRO-017', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (28, 'CARRO-018', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (29, 'CARRO-019', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (30, 'CARRO-020', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (31, 'CARRO-021', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (32, 'CARRO-022', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (33, 'CARRO-023', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (34, 'CARRO-024', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (35, 'CARRO-025', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (36, 'CARRO-026', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (37, 'CARRO-027', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (38, 'CARRO-028', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (39, 'CARRO-029', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (40, 'CARRO-030', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (41, 'CARRO-031', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (42, 'CARRO-032', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (43, 'CARRO-033', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (44, 'CARRO-034', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (45, 'CARRO-035', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (46, 'CARRO-036', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (47, 'CARRO-037', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (48, 'CARRO-038', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (49, 'CARRO-039', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (50, 'CARRO-040', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (51, 'CARRO-041', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (52, 'CARRO-042', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (53, 'CARRO-043', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (54, 'CARRO-044', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (55, 'CARRO-045', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (56, 'CARRO-046', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (57, 'CARRO-047', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (58, 'CARRO-048', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (59, 'CARRO-049', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (60, 'CARRO-050', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (61, 'CARRO-051', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (62, 'CARRO-052', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (63, 'CARRO-053', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (64, 'CARRO-054', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (65, 'CARRO-055', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (66, 'CARRO-056', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (67, 'CARRO-057', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (68, 'CARRO-058', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (69, 'CARRO-059', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (70, 'CARRO-060', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (71, 'CARRO-061', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (72, 'CARRO-062', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (73, 'CARRO-063', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (74, 'CARRO-064', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (75, 'CARRO-065', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (76, 'CARRO-066', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (77, 'CARRO-067', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (78, 'CARRO-068', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (79, 'CARRO-069', 'CARRO');
INSERT INTO public.celda OVERRIDING SYSTEM VALUE VALUES (80, 'CARRO-070', 'CARRO');


--
-- Data for Name: cliente; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cliente OVERRIDING SYSTEM VALUE VALUES (1, 'Juan Pérez', '1000100010', '3101112222');
INSERT INTO public.cliente OVERRIDING SYSTEM VALUE VALUES (2, 'María Torres', '1000200020', '3102223333');
INSERT INTO public.cliente OVERRIDING SYSTEM VALUE VALUES (3, 'Andrés López', '1000300030', '3103334444');


--
-- Data for Name: estancia; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: operador; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.operador OVERRIDING SYSTEM VALUE VALUES (1, 'Laura Gómez', '3001112222', 'operador.dia', 'pbkdf2_sha256$390000$aae352d8701081e614ab7f4cae1b9917$53e4996273f3778bb535b51f2b474376a967db683b98f2a006d4032a454d899d', 'DIA', 'OPERADOR');
INSERT INTO public.operador OVERRIDING SYSTEM VALUE VALUES (2, 'Carlos Ruiz', '3003334444', 'admin', 'pbkdf2_sha256$390000$47644f18e9bc6174fc5246aaba271ca6$4f3bba0721c2f73c48c75bd4d31f8a7317e4b83c5613d2c14f238df9accaaf1a', 'NOCHE', 'ADMINISTRADOR');


--
-- Data for Name: pago; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.pago OVERRIDING SYSTEM VALUE VALUES (1, 1, 1, 250000.00, '2026-11-22', '2026-12-21', '2026-11-22 16:49:48.440833+00');
INSERT INTO public.pago OVERRIDING SYSTEM VALUE VALUES (2, 2, 1, 250000.00, '2026-11-22', '2026-12-21', '2026-11-22 16:49:48.440833+00');
INSERT INTO public.pago OVERRIDING SYSTEM VALUE VALUES (3, 3, 1, 100000.00, '2026-11-22', '2026-12-21', '2026-11-22 16:49:48.440833+00');
INSERT INTO public.pago OVERRIDING SYSTEM VALUE VALUES (4, 4, 1, 250000.00, '2026-11-22', '2026-12-21', '2026-11-22 16:49:48.440833+00');


--
-- Data for Name: token_revocado; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: vehiculo; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.vehiculo OVERRIDING SYSTEM VALUE VALUES (1, 'ABC123', 'Rojo', 2021, 'Mazda', 'AUTOMOVIL', 1);
INSERT INTO public.vehiculo OVERRIDING SYSTEM VALUE VALUES (2, 'XYZ789', 'Azul', 2019, 'Chevrolet', 'CAMIONETA', 1);
INSERT INTO public.vehiculo OVERRIDING SYSTEM VALUE VALUES (3, 'MOT001', 'Negro', 2022, 'Yamaha', 'MOTO', 2);
INSERT INTO public.vehiculo OVERRIDING SYSTEM VALUE VALUES (4, 'DEF456', 'Blanco', 2020, 'Renault', 'AUTOMOVIL', 3);


--
-- Name: celda_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.celda_id_seq', 80, true);


--
-- Name: cliente_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cliente_id_seq', 3, true);


--
-- Name: estancia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.estancia_id_seq', 1, false);


--
-- Name: operador_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.operador_id_seq', 2, true);


--
-- Name: pago_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.pago_id_seq', 4, true);


--
-- Name: vehiculo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.vehiculo_id_seq', 4, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: celda celda_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.celda
    ADD CONSTRAINT celda_pkey PRIMARY KEY (id);


--
-- Name: cliente cliente_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_pkey PRIMARY KEY (id);


--
-- Name: estancia estancia_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estancia
    ADD CONSTRAINT estancia_pkey PRIMARY KEY (id);


--
-- Name: operador operador_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.operador
    ADD CONSTRAINT operador_pkey PRIMARY KEY (id);


--
-- Name: pago pago_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pago
    ADD CONSTRAINT pago_pkey PRIMARY KEY (id);


--
-- Name: token_revocado pk_token_revocado; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_revocado
    ADD CONSTRAINT pk_token_revocado PRIMARY KEY (jti);


--
-- Name: celda uq_celda_codigo; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.celda
    ADD CONSTRAINT uq_celda_codigo UNIQUE (codigo);


--
-- Name: cliente uq_cliente_documento; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT uq_cliente_documento UNIQUE (documento);


--
-- Name: operador uq_operador_usuario; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.operador
    ADD CONSTRAINT uq_operador_usuario UNIQUE (usuario);


--
-- Name: vehiculo uq_vehiculo_placa; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vehiculo
    ADD CONSTRAINT uq_vehiculo_placa UNIQUE (placa);


--
-- Name: vehiculo vehiculo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vehiculo
    ADD CONSTRAINT vehiculo_pkey PRIMARY KEY (id);


--
-- Name: ix_estancia_vehiculo_entrada; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_estancia_vehiculo_entrada ON public.estancia USING btree (vehiculo_id, entrada);


--
-- Name: ix_pago_vehiculo_periodo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_pago_vehiculo_periodo ON public.pago USING btree (vehiculo_id, periodo_fin);


--
-- Name: ix_token_revocado_expira; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_token_revocado_expira ON public.token_revocado USING btree (expira);


--
-- Name: uq_estancia_celda_abierta; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_estancia_celda_abierta ON public.estancia USING btree (celda_id) WHERE (salida IS NULL);


--
-- Name: uq_estancia_vehiculo_abierta; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_estancia_vehiculo_abierta ON public.estancia USING btree (vehiculo_id) WHERE (salida IS NULL);


--
-- Name: estancia fk_estancia_celda; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estancia
    ADD CONSTRAINT fk_estancia_celda FOREIGN KEY (celda_id) REFERENCES public.celda(id) ON DELETE RESTRICT;


--
-- Name: estancia fk_estancia_operador_entrada; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estancia
    ADD CONSTRAINT fk_estancia_operador_entrada FOREIGN KEY (operador_entrada_id) REFERENCES public.operador(id) ON DELETE RESTRICT;


--
-- Name: estancia fk_estancia_operador_salida; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estancia
    ADD CONSTRAINT fk_estancia_operador_salida FOREIGN KEY (operador_salida_id) REFERENCES public.operador(id) ON DELETE RESTRICT;


--
-- Name: estancia fk_estancia_vehiculo; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estancia
    ADD CONSTRAINT fk_estancia_vehiculo FOREIGN KEY (vehiculo_id) REFERENCES public.vehiculo(id) ON DELETE RESTRICT;


--
-- Name: pago fk_pago_operador; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pago
    ADD CONSTRAINT fk_pago_operador FOREIGN KEY (operador_id) REFERENCES public.operador(id) ON DELETE RESTRICT;


--
-- Name: pago fk_pago_vehiculo; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pago
    ADD CONSTRAINT fk_pago_vehiculo FOREIGN KEY (vehiculo_id) REFERENCES public.vehiculo(id) ON DELETE RESTRICT;


--
-- Name: vehiculo fk_vehiculo_cliente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vehiculo
    ADD CONSTRAINT fk_vehiculo_cliente FOREIGN KEY (cliente_id) REFERENCES public.cliente(id) ON DELETE RESTRICT;


--
-- PostgreSQL database dump complete
--

\unrestrict 3OOIa7dgMG9tEvjWDSowB60cw7mjehCluHnebZnQR7ewY2vbgUag8EZZB5kjTLp

