/* -*- c++ -*- */
#ifndef _SNMP_VARS_H_
#define _SNMP_VARS_H_

/**********************************************************************
 *
 *           Copyright 1998 by Carnegie Mellon University
 * 
 *                       All Rights Reserved
 * 
 * Permission to use, copy, modify, and distribute this software and its
 * documentation for any purpose and without fee is hereby granted,
 * provided that the above copyright notice appear in all copies and that
 * both that copyright notice and this permission notice appear in
 * supporting documentation, and that the name of CMU not be
 * used in advertising or publicity pertaining to distribution of the
 * software without specific, written prior permission.
 * 
 * CMU DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
 * ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL
 * CMU BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
 * ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
 * WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
 * ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
 * SOFTWARE.
 * 
 * Author: Ryan Troll <ryan+@andrew.cmu.edu>
 * 
 * $Id: snmp_vars.h,v 1.12 1998/05/06 04:07:52 ryan Exp $
 * 
 **********************************************************************/

struct variable_list {
    struct variable_list *next_variable;    /* NULL for last variable */
    oid	    *name;  /* Object identifier of variable */
    int	    name_length;    /* number of subid's in name */
    u_char  type;   /* ASN type of variable */
    union { /* value of variable */
	int	*integer;
	u_char	*string;
	oid	*objid;
    } val;
    int	    val_len;
};

#ifdef WIN32
#define DLLEXPORT __declspec(dllexport)
#else  /* WIN32 */
#define DLLEXPORT
#endif /* WIN32 */

#ifdef __cplusplus
extern "C" {
#endif

DLLEXPORT  struct variable_list *snmp_var_new(oid *, int);
DLLEXPORT  struct variable_list *snmp_var_clone(struct variable_list *);
DLLEXPORT  void snmp_var_free(struct variable_list *);

DLLEXPORT  u_char *snmp_var_EncodeVarBind(u_char *, int *, struct variable_list *, int);
DLLEXPORT  u_char *snmp_var_DecodeVarBind(u_char *, int *, struct variable_list **, int);

#ifdef __cplusplus
}
#endif

#define MAX_NAME_LEN	64  /* number of subid's in a objid */

/*
 * RFC 1902: Structure of Management Information for SNMPv2
 *
 * Defined Types
 *
 */

#define SMI_INTEGER     ASN_INTEGER
#define SMI_STRING      ASN_OCTET_STR
#define SMI_OBJID       ASN_OBJECT_ID
#define SMI_NULLOBJ     ASN_NULL
#define SMI_IPADDRESS  (ASN_APPLICATION | 0) /* OCTET STRING, net byte order */
#define SMI_COUNTER32  (ASN_APPLICATION | 1) /* INTEGER */
#define SMI_GAUGE32    (ASN_APPLICATION | 2) /* INTEGER */
# define SMI_UNSIGNED32 SMI_GAUGE32
#define SMI_TIMETICKS  (ASN_APPLICATION | 3) /* INTEGER */
#define SMI_OPAQUE     (ASN_APPLICATION | 4) /* OCTET STRING */

#define SMI_COUNTER64  (ASN_APPLICATION | 6) /* INTEGER */

#define SMI_NOSUCHOBJECT   (ASN_CONTEXT | ASN_PRIMITIVE | 0x0)
#define SMI_NOSUCHINSTANCE (ASN_CONTEXT | ASN_PRIMITIVE | 0x1)
#define SMI_ENDOFMIBVIEW   (ASN_CONTEXT | ASN_PRIMITIVE | 0x2)


#endif /* _SNMP_VARS_H_ */
