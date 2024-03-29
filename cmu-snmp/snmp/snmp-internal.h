/* -*- c++ -*- */
#ifndef _SNMP_INTERNAL_H_
#define _SNMP_INTERNAL_H_

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
 * $Id: snmp-internal.h,v 1.8 1998/05/06 04:07:11 ryan Exp $
 * 
 **********************************************************************/

#define SNMP_PORT	    161
#define SNMP_TRAP_PORT	    162
#define SNMP_MAX_LEN	    484

#ifndef ERROR
#ifdef DEBUG
#define ERROR(string)	printf("%s(%d): %s\n",__FILE__, __LINE__, string);
#else
#define ERROR(string)
#endif
#endif /* ERROR */

#endif /* _SNMP_INTERNAL_H_ */
