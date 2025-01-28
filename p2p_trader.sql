--
-- PostgreSQL database dump
--

-- Dumped from database version 14.8 (Ubuntu 14.8-1.pgdg20.04+1)
-- Dumped by pg_dump version 14.15 (Homebrew)

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
-- Name: phone_numbers; Type: TABLE; Schema: public; Owner: gen_user
--

CREATE TABLE public.phone_numbers (
    id bigint NOT NULL,
    number character varying,
    name character varying,
    created_at timestamp(6) without time zone NOT NULL,
    updated_at timestamp(6) without time zone NOT NULL,
    session_string character varying,
    token character varying,
    platform character varying,
    telegram_id character varying,
    state character varying DEFAULT 'created'::character varying,
);


ALTER TABLE public.phone_numbers OWNER TO gen_user;

--
-- Name: phone_numbers_id_seq; Type: SEQUENCE; Schema: public; Owner: gen_user
--

CREATE SEQUENCE public.phone_numbers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.phone_numbers_id_seq OWNER TO gen_user;

--
-- Name: phone_numbers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gen_user
--

ALTER SEQUENCE public.phone_numbers_id_seq OWNED BY public.phone_numbers.id;


--
-- Name: phone_numbers id; Type: DEFAULT; Schema: public; Owner: gen_user
--

ALTER TABLE ONLY public.phone_numbers ALTER COLUMN id SET DEFAULT nextval('public.phone_numbers_id_seq'::regclass);


--
-- Name: phone_numbers phone_numbers_pkey; Type: CONSTRAINT; Schema: public; Owner: gen_user
--

ALTER TABLE ONLY public.phone_numbers
    ADD CONSTRAINT phone_numbers_pkey PRIMARY KEY (id);


--
-- Name: TABLE phone_numbers; Type: ACL; Schema: public; Owner: gen_user
--

GRANT ALL ON TABLE public.phone_numbers TO adfsnsdfjk;


--
-- Name: SEQUENCE phone_numbers_id_seq; Type: ACL; Schema: public; Owner: gen_user
--

REVOKE ALL ON SEQUENCE public.phone_numbers_id_seq FROM gen_user;
GRANT SELECT,UPDATE ON SEQUENCE public.phone_numbers_id_seq TO gen_user;
GRANT SELECT,UPDATE ON SEQUENCE public.phone_numbers_id_seq TO adfsnsdfjk;


--
-- PostgreSQL database dump complete
--

