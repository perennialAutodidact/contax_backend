import React, { useEffect } from "react";
import { useDispatch } from "react-redux";
import { Link, useParams } from "react-router-dom";
import { Fade } from "reactstrap";
import formatPhoneNumber from "../../utils/formatPhoneNumber";

import {
  AiOutlinePhone,
  AiOutlineMail,
  AiOutlineDelete,
  AiOutlineEdit,
  AiOutlineCheckCircle,
  AiOutlineCloseCircle,
  AiOutlineFileText,
} from "react-icons/ai";
import { Row, Col } from "reactstrap";

import ContactAvatar from "../../components/Avatar";
import ContactDeletePopover from "./ContactDeletePopover";

import { setCurrentContact } from "../../state/ContactSlice";
import { sortNotes } from "../../state/NoteSlice";

import "./scss/ContactItem.scss";

const ContactItem = ({
  contact,
  togglePopover,
  popoverIsOpen,
  onDeleteContact,
  filterBy,
  filterQuery,
}) => {
  const dispatch = useDispatch();
  const { contactId } = useParams();

  const { firstName, lastName, email, primaryPhone } = contact;

  useEffect(() => {
    if (filterBy === "notes") {
      dispatch(sortNotes({ notes: contact.notes, filterQuery }));
    }
  }, [filterBy, filterQuery, sortNotes]);

  return (
    <Col
      sm={12}
      className="px-0 pb-2 mb-3 pb-md-3 mb-md-4 contact-item shadow rounded"
      id={`contact-${contact.id}`}
    >
      <Row className="contact-body pb-3 position-relative rounded ">
        {/* <ContactDeletePopover
          togglePopover={togglePopover}
          popoverIsOpen={popoverIsOpen}
          onDeleteContact={onDeleteContact}
          contact={contact}
        /> */}
        {/* DELETE CONTACT POPOVER */}
        {/* <Fade
          in={popoverIsOpen}
          className={
            "delete-contact-popover g-0 position-absolute " +
            "border border-secondary rounded px-0 " +
            (popoverIsOpen ? "d-block" : "d-none")
          }
        >
          <Row className="g-0 h-100">
            <Col
              xs={12}
              className="
                delete-contact-popover-header
                text-center
                p-4
                lead
                d-flex
                align-items-center
                justify-content-center
              "
              onClick={() => {
                togglePopover(contact.id, !popoverIsOpen);
              }}
            >
              <span>
                Delete <br />
                {firstName} {lastName}?
              </span>
            </Col>
            <Col
              xs={{ size: 8, offset: 2 }}
              md={{ size: 6, offset: 3 }}
              className="
                delete-contact-popover-body
                d-flex
                align-items-center
                justify-content-around
                pb-5 pt-3 pt-md-4
              "
            >
              <span
                className="
                  crud-icon delete-confirm-icon
                  d-flex
                  align-items-center
                  justify-content-center
                "
                onClick={() => onDeleteContact(contact.id)}
              >
                <AiOutlineCheckCircle />
              </span>
              <span
                className="
                  crud-icon delete-cancel-icon
                  d-flex
                  align-items-center
                  justify-content-center
                "
                onClick={() => togglePopover(contact.id, !popoverIsOpen)}
              >
                <AiOutlineCloseCircle />
              </span>
            </Col>
          </Row>
        </Fade> */}

        {/* AVATAR */}
        <Row
          tag={Link}
          to={`/app/detail/${contact.id}`}
          onClick={() => {
            dispatch(setCurrentContact(contact));
          }}
          className="
            contact-item-header
            g-0
            bg-secondary
            rounded-top
            py-3
            border-bottom
            border-info
            border-3
            text-decoration-none
          "
        >
          <Col xs={12} md={2} className="d-flex justify-content-center">
            <ContactAvatar contact={contact} />
          </Col>

          <Col
            xs={12}
            md={10}
            className="
              contact-field
              name-field
              border-bottom
              border-secondary
              mt-2 mt-md-0
              d-flex
              align-items-end justify-content-center
              align-items-md-center justify-content-md-start
            "
          >
            <span>
              {firstName} {lastName}
            </span>
          </Col>
        </Row>

        {/* NAME, EMAIL AND PHONE */}
        <Row className="g-0 px-4 px-md-3 mt-4 small">
          <Col
            xs={2}
            className="
              field-icon
              border-bottom
              border-secondary
              mb-3
              mb-md-4
              d-flex
              justify-content-center
              align-items-center
            "
          >
            <AiOutlineMail className="text-secondary" />
          </Col>
          <Col
            xs={10}
            className="contact-field border-bottom border-secondary mb-3 mb-md-4"
          >
            {email ? email : "Not Provided"}
          </Col>

          <Col
            xs={2}
            className="
              field-icon
              border-bottom
              border-secondary
              d-flex
              justify-content-center
              align-items-center
              mb-3
              mb-md-4
            "
          >
            <AiOutlinePhone className="text-secondary" />
          </Col>
          <Col
            xs={10}
            className="
              contact-field
              border-bottom
              border-secondary
              mb-3
              mb-md-4
            "
          >
            {contact[`${primaryPhone.toLowerCase()}PhoneNumber`] ? (
              <span>
                {formatPhoneNumber(
                  contact[`${primaryPhone.toLowerCase()}PhoneNumber`]
                )}
              </span>
            ) : (
              "Not Provided"
            )}
          </Col>
          {contact.notes !== [] && (
            <>
              <Col
                xs={2}
                className="
                  field-icon
                  border-bottom
                  border-secondary
                  d-flex
                  justify-content-center
                "
              >
                <AiOutlineFileText className="text-secondary" />
              </Col>
              <Col
                xs={10}
                className="contact-field border-bottom border-secondary"
              >
                {contact.notes.length > 0 &&
                  contact.notes.map((note, i) => <div>&bull; {note.text}</div>)}
              </Col>
            </>
          )}
        </Row>

        <Col
          xs={12}
          className="d-flex align-items-center justify-content-end mt-3"
        >
          <Link to={`/app/edit/${contact.id}`}>
            <AiOutlineEdit
              className="crud-icon edit-icon m-2"
              onClick={() => {
                dispatch(setCurrentContact(contact));
              }}
            />
          </Link>
          <span className="position-relative">
            <AiOutlineDelete
              id={`contact-${contact.id}-popover`}
              className="crud-icon delete-icon m-2"
              onClick={() => togglePopover(contact.id, !popoverIsOpen)}
            />
          </span>
        </Col>
      </Row>
    </Col>
  );
};

export default ContactItem;
